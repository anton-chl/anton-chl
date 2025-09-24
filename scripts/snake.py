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
GRID_COLOR = "#161b22"    # subtle grid outline
RADIUS = 4                # corner radius for rounded squares

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

        # candidate moves
        valid_moves = []
        for dx, dy in directions:
            nx, ny = head[0] + dx, head[1] + dy
            if 0 <= nx < width and 0 <= ny < height:
                # block direct reversal
                if len(snake) > 1 and (nx, ny) == snake[-2]:
                    continue
                valid_moves.append((dx, dy))

        if not valid_moves:
            break

        move = random.choice(valid_moves)
        new_head = (head[0] + move[0], head[1] + move[1])
        snake.append(new_head)

        # trim to fixed length
        while len(snake) > SNAKE_LENGTH:
            snake.pop(0)

        # eat food
        if new_head in food_positions:
            eaten.add(new_head)

        frames.append(render_frame(width, height, snake, food_positions, eaten))

    return frames

# === STEP 3: Rounded-square drawing helper ===
def draw_cell(draw, x, y, color):
    x0, y0 = x * GRID_CELL + 2, y * GRID_CELL + 2
    x1, y1 = x0 + GRID_CELL - 4, y0 + GRID_CELL - 4
    draw.rounded_rectangle([x0, y0, x1, y1], radius=RADIUS, fill=color, outline=GRID_COLOR, width=1)

# === STEP 4: Render frame ===
def render_frame(width, height, snake, food, eaten):
    img = Image.new("RGB", (width * GRID_CELL, height * GRID_CELL), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # draw background grid (empty cells)
    for x in range(width):
        for y in range(height):
            draw_cell(draw, x, y, BG_COLOR)

    # draw uneaten food
    for fx, fy in food:
        if (fx, fy) not in eaten:
            draw_cell(draw, fx, fy, FOOD_COLOR)

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
        draw_cell(draw, sx, sy, color)

    return img

# === STEP 5: Save GIF ===
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
