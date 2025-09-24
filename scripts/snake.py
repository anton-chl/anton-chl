import os
import requests
import random
from PIL import Image, ImageDraw

# === CONFIG ===
USERNAME = "anton-chl"
TOKEN = os.environ.get("GITHUB_TOKEN")  # GitHub token in repo secrets
GRID_CELL = 20   # size of each cell in pixels
FPS = 5          # frames per second
SNAKE_LENGTH = 15
GIF_NAME = "snake.gif"

# Colors
BG_COLOR = "#0d1117"      # dark GitHub background
FOOD_COLOR = "#196127"    # GitHub green
EATEN_COLOR = "#30363d"   # grey-blue after eaten

# === STEP 1: Fetch contributions grid ===
def fetch_contributions(username):
    url = "https://api.github.com/graphql"
    query = """
    query($login:String!){
      user(login:$login){
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    headers = {"Authorization": f"Bearer {TOKEN}"}
    resp = requests.post(url, json={"query": query, "variables": {"login": username}}, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

    grid = []
    for col, week in enumerate(weeks):
        for row, day in enumerate(week["contributionDays"]):
            if day["contributionCount"] > 0:
                grid.append((col, row))  # food
    return grid, len(weeks)

# === STEP 2: Random-walk snake ===
def simulate_snake(food_positions, width, height=7):
    snake = [(0, 0)]  # starting head
    frames = []
    eaten = set()

    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    steps = width * height * 4

    for _ in range(steps):
        head = snake[-1]

        # pick valid random move
        valid_moves = []
        for dx, dy in directions:
            nx, ny = head[0] + dx, head[1] + dy
            if 0 <= nx < width and 0 <= ny < height:
                valid_moves.append((nx, ny))
        if not valid_moves:
            break

        new_head = random.choice(valid_moves)
        snake.append(new_head)

        # trim to fixed length
        while len(snake) > SNAKE_LENGTH:
            snake.pop(0)

        # eat food (turns grey)
        if new_head in food_positions:
            eaten.add(new_head)

        frames.append(render_frame(width, height, snake, food_positions, eaten))

    return frames

# === STEP 3: Render frame ===
def render_frame(width, height, snake, food, eaten):
    img = Image.new("RGB", (width * GRID_CELL, height * GRID_CELL), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # draw food
    for fx, fy in food:
        color = FOOD_COLOR if (fx, fy) not in eaten else EATEN_COLOR
        x0, y0 = fx * GRID_CELL, fy * GRID_CELL
        x1, y1 = x0 + GRID_CELL - 2, y0 + GRID_CELL - 2
        draw.rectangle([x0, y0, x1, y1], fill=color)

    # draw snake
    for i, (sx, sy) in enumerate(snake):
        if i == len(snake) - 1:
            color = "#ff69b4"  # head pink
        else:
            # purple→pink gradient
            ratio = i / len(snake)
            r = int(255 * (1 - ratio) + 138 * ratio)
            g = int(105 * (1 - ratio) + 43 * ratio)
            b = int(180 * (1 - ratio) + 226 * ratio)
            color = (r, g, b)
        x0, y0 = sx * GRID_CELL, sy * GRID_CELL
        x1, y1 = x0 + GRID_CELL - 2, y0 + GRID_CELL - 2
        draw.rectangle([x0, y0, x1, y1], fill=color)

    return img

# === STEP 4: Save GIF ===
def save_gif(frames, filename):
    frames[0].save(
        filename,
        save_all=True,
        append_images=frames[1:],
        optimize=False,
        duration=int(1000 / FPS),
        loop=0,
    )

if __name__ == "__main__":
    food, width = fetch_contributions(USERNAME)
    frames = simulate_snake(food, width)
    save_gif(frames, GIF_NAME)
    print(f"✅ Snake GIF saved as {GIF_NAME}")
