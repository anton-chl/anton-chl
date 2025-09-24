import os
import requests
import random

# === CONFIG ===
USERNAME = "anton-chl"
TOKEN = os.environ.get("GITHUB_TOKEN")
GRID_CELL = 20
SNAKE_LENGTH = 15
SVG_NAME = "snake.svg"
FRAMES = 500   # number of animation steps
FRAME_MS = 120 # duration per frame in milliseconds

# Colors
BG_COLOR = "#161b22"   # GitHub dark blue background
GRID_COLOR = "#21262d" # subtle grid outline
LEVEL_COLORS = [
    "#0e4429",  # darkest green
    "#006d32",
    "#26a641",
    "#39d353",  # lightest green
]

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

    food = {}
    width = len(weeks)
    for col, week in enumerate(weeks):
        for row, day in enumerate(week["contributionDays"]):
            count = day["contributionCount"]
            if count > 0:
                # Scale contribution count into GitHub green levels
                if count >= 20:
                    level = 0
                elif count >= 10:
                    level = 1
                elif count >= 5:
                    level = 2
                else:
                    level = 3
                food[(col, row)] = LEVEL_COLORS[level]
    return food, width

# === STEP 2: Random snake movement (avoids self + walls) ===
def simulate_snake(food_positions, width, height=7):
    snake = [(0, 0)]
    eaten = set()
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    positions = []

    for _ in range(FRAMES):
        head = snake[-1]
        valid_moves = []
        for dx, dy in directions:
            nx, ny = head[0] + dx, head[1] + dy
            if 0 <= nx < width and 0 <= ny < height:
                if len(snake) > 1 and (nx, ny) == snake[-2]:
                    continue  # no reversal
                if (nx, ny) in snake:
                    continue  # no self collision
                valid_moves.append((dx, dy))
        if not valid_moves:
            break
        move = random.choice(valid_moves)
        new_head = (head[0] + move[0], head[1] + move[1])
        snake.append(new_head)
        while len(snake) > SNAKE_LENGTH:
            snake.pop(0)
        if new_head in food_positions:
            eaten.add(new_head)
        positions.append((list(snake), set(eaten)))
    return positions

# === STEP 3: Generate SVG ===
def generate_svg(positions, food, width, height=7):
    svg_width = width * GRID_CELL
    svg_height = height * GRID_CELL
    dur = FRAMES * FRAME_MS / 1000  # total duration in seconds

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">']
    svg.append(f'<rect width="100%" height="100%" fill="{BG_COLOR}"/>')

    # grid cells
    for x in range(width):
        for y in range(height):
            x0, y0 = x * GRID_CELL + 2, y * GRID_CELL + 2
            size = GRID_CELL - 4
            svg.append(f'<rect x="{x0}" y="{y0}" width="{size}" height="{size}" rx="4" ry="4" fill="{BG_COLOR}" stroke="{GRID_COLOR}" stroke-width="1"/>')

    # food cells
    for (fx, fy), color in food.items():
        x0, y0 = fx * GRID_CELL + 2, fy * GRID_CELL + 2
        size = GRID_CELL - 4
        svg.append(f'<rect x="{x0}" y="{y0}" width="{size}" height="{size}" rx="4" ry="4" fill="{color}" class="food-{fx}-{fy}"/>')

    # animation frames
    svg.append(f'<g id="snake">')
    for frame, (snake, eaten) in enumerate(positions):
        t_start = frame * FRAME_MS / 1000
        t_end = (frame + 1) * FRAME_MS / 1000
        visibility = "visible" if frame == 0 else "hidden"
        svg.append(f'<g id="f{frame}" visibility="{visibility}">')

        # snake body
        for i, (sx, sy) in enumerate(snake):
            if i == len(snake) - 1:
                color = "#ff69b4"  # head pink
            else:
                ratio = i / len(snake)
                r = int(255 * (1 - ratio) + 138 * ratio)
                g = int(105 * (1 - ratio) + 43 * ratio)
                b = int(180 * (1 - ratio) + 226 * ratio)
                color = f'rgb({r},{g},{b})'
            x0, y0 = sx * GRID_CELL + 2, sy * GRID_CELL + 2
            size = GRID_CELL - 4
            svg.append(f'<rect x="{x0}" y="{y0}" width="{size}" height="{size}" rx="4" ry="4" fill="{color}"/>')

        # eaten food disappears
        for (fx, fy) in eaten:
            x0, y0 = fx * GRID_CELL + 2, fy * GRID_CELL + 2
            size = GRID_CELL - 4
            svg.append(f'<rect x="{x0}" y="{y0}" width="{size}" height="{size}" rx="4" ry="4" fill="{BG_COLOR}" stroke="{GRID_COLOR}" stroke-width="1"/>')

        svg.append(f'<set attributeName="visibility" to="visible" begin="{t_start}s" end="{t_end}s"/>')
        svg.append('</g>')
    svg.append('</g>')

    # infinite loop
    svg.append(f'<animate href="#snake" attributeName="visibility" from="visible" to="visible" dur="{dur}s" repeatCount="indefinite"/>')
    svg.append('</svg>')

    with open(SVG_NAME, "w") as f:
        f.write("\n".join(svg))

if __name__ == "__main__":
    food, width = fetch_contributions(USERNAME)
    positions = simulate_snake(food, width)
    generate_svg(positions, food, width)
    print(f"✅ Snake SVG saved as {SVG_NAME}")
