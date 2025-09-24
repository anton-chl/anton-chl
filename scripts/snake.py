import os
import requests
import datetime
from PIL import Image, ImageDraw

# === CONFIG ===
USERNAME = "anton-chl"
TOKEN = os.environ.get("GITHUB_TOKEN")  # GitHub token in repo secrets
GRID_CELL = 20   # size of each cell in pixels
FPS = 5          # frames per second
GIF_NAME = "snake.gif"

# === STEP 1: Fetch contributions from GitHub GraphQL ===
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
                grid.append((col, row))  # food coordinates
    return grid, len(weeks)

# === STEP 2: Snake simulation ===
def simulate_snake(food_positions, width, height=7):
    snake = [(0, 0)]  # starting head
    direction = (1, 0)  # move right
    frames = []
    eaten = set()

    max_steps = width * height * 2
    for step in range(max_steps):
        head = snake[-1]
        new_head = (head[0] + direction[0], head[1] + direction[1])

        # change direction at bounds
        if new_head[0] >= width:
            new_head = (head[0], head[1] + 1)
            direction = (0, 1)
        if new_head[1] >= height:
            new_head = (head[0] - 1, head[1])
            direction = (-1, 0)
        if new_head[0] < 0:
            new_head = (head[0], head[1] - 1)
            direction = (0, -1)
        if new_head[1] < 0:
            new_head = (head[0] + 1, head[1])
            direction = (1, 0)

        snake.append(new_head)

        # eat food → grow
        if new_head in food_positions and new_head not in eaten:
            eaten.add(new_head)
        else:
            snake.pop(0)  # move without growing

        frames.append(render_frame(width, height, snake, food_positions, eaten))

    return frames

# === STEP 3: Rendering ===
def render_frame(width, height, snake, food, eaten):
    img = Image.new("RGB", (width * GRID_CELL, height * GRID_CELL), "white")
    draw = ImageDraw.Draw(img)

    # draw food
    for fx, fy in food:
        color = "#196127" if (fx, fy) not in eaten else "#eeeeee"
        x0, y0 = fx * GRID_CELL, fy * GRID_CELL
        x1, y1 = x0 + GRID_CELL - 2, y0 + GRID_CELL - 2
        draw.rectangle([x0, y0, x1, y1], fill=color)

    # draw snake body
    for i, (sx, sy) in enumerate(snake):
        if i == len(snake) - 1:
            color = "#ff69b4"  # head pink
        else:
            # gradient from purple to pink
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
