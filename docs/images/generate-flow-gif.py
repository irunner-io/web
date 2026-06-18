#!/usr/bin/env python3
"""Generate animated GIF showing iRunner continuous compute flow."""

from PIL import Image, ImageDraw, ImageFont
import os

W, H = 900, 500
FRAMES = 60
DURATION = 120  # ms per frame

# Colors
BG = (20, 15, 46)
SURFACE = (26, 20, 64)
CARD = (33, 26, 74)
BORDER = (61, 52, 112)
TEXT = (240, 240, 242)
TEXT_SEC = (184, 178, 208)
TEXT_DIM = (122, 116, 148)
GREEN = (46, 221, 146)
PURPLE = (124, 92, 252)
PURPLE_DIM = (91, 63, 212)
RED = (248, 113, 113)
BLUE = (96, 165, 250)
YELLOW = (250, 204, 21)

def get_font(size):
    """Try to load a nice font, fall back to default."""
    paths = [
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/opt/homebrew/share/fonts/JetBrainsMono-Regular.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

font_sm = get_font(11)
font_md = get_font(13)
font_lg = get_font(16)
font_xl = get_font(20)

# Job definitions that cycle through
JOBS = [
    {"name": "build", "label": "ir-ecs-2cpu-4g", "backend": "ECS", "color": GREEN},
    {"name": "test", "label": "ir-ec2-large", "backend": "EC2", "color": BLUE},
    {"name": "deploy", "label": "ir-eks-small", "backend": "EKS", "color": YELLOW},
    {"name": "lint", "label": "ir-ecs-small", "backend": "ECS", "color": GREEN},
    {"name": "docker", "label": "ir-ec2-gpu", "backend": "EC2", "color": BLUE},
    {"name": "integration", "label": "ir-eks-medium", "backend": "EKS", "color": YELLOW},
]

def draw_rounded_rect(draw, xy, radius, fill=None, outline=None):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline)

def draw_box(draw, x, y, w, h, fill=CARD, border=BORDER, radius=8):
    draw_rounded_rect(draw, (x, y, x+w, y+h), radius, fill=fill, outline=border)

def lerp(a, b, t):
    return a + (b - a) * t

def draw_arrow(draw, x1, y1, x2, y2, color, progress=1.0):
    """Draw an animated arrow with a traveling dot."""
    draw.line([(x1, y1), (x2, y2)], fill=(*color, 100), width=2)
    # Traveling dot
    dx = lerp(x1, x2, progress)
    dy = lerp(y1, y2, progress)
    draw.ellipse((dx-4, dy-4, dx+4, dy+4), fill=color)

def generate_frame(frame_num):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    t = frame_num / FRAMES  # 0.0 to 1.0
    cycle = frame_num % 20  # sub-cycle for individual animations
    job_idx = (frame_num // 10) % len(JOBS)

    # Title
    draw.text((W//2 - 120, 12), "How iRunner Works", fill=TEXT, font=font_xl)

    # === LEFT: GitHub Workflows ===
    draw_box(draw, 20, 50, 200, 200, fill=SURFACE)
    draw.text((60, 58), "GITHUB WORKFLOWS", fill=TEXT_DIM, font=font_sm)

    # Show rotating jobs
    for i in range(3):
        idx = (job_idx + i) % len(JOBS)
        job = JOBS[idx]
        y_pos = 82 + i * 52
        alpha = 255 if i == 0 else 150

        draw_box(draw, 32, y_pos, 176, 44, fill=(26, 20, 64))
        draw.text((42, y_pos + 6), f"jobs.{job['name']}:", fill=TEXT_SEC, font=font_sm)
        draw.text((42, y_pos + 22), f"runs-on: {job['label']}", fill=job['color'], font=font_sm)

    # Pulsing "new job" indicator
    if cycle < 10:
        pulse = abs(cycle - 5) / 5.0
        r = int(6 + pulse * 3)
        draw.ellipse((205 - r, 55 - r, 205 + r, 55 + r), fill=GREEN)

    # === MIDDLE: Control Plane ===
    draw_box(draw, 270, 50, 200, 200, fill=SURFACE)
    draw.text((290, 58), "iR CONTROL PLANE", fill=TEXT_DIM, font=font_sm)

    # Pool matching animation
    current_job = JOBS[job_idx]
    draw_box(draw, 282, 82, 176, 36, fill=(26, 20, 64), border=PURPLE)
    draw.text((292, 89), "Label matching", fill=PURPLE, font=font_md)
    draw.text((292, 104), current_job['label'], fill=TEXT_SEC, font=font_sm)

    # Pool selection
    draw_box(draw, 282, 126, 176, 36, fill=(26, 20, 64))
    draw.text((292, 133), f"Pool: {current_job['backend']}", fill=TEXT, font=font_md)

    # Provisioning state
    if cycle < 8:
        state_text = "Provisioning..."
        state_color = YELLOW
    else:
        state_text = "Running"
        state_color = GREEN

    draw_box(draw, 282, 170, 176, 36, fill=(26, 20, 64))
    draw.ellipse((292, 181, 300, 189), fill=state_color)
    draw.text((306, 177), state_text, fill=state_color, font=font_md)

    # Active count
    active = 2 + (frame_num % 4)
    draw_box(draw, 282, 214, 176, 28, fill=(26, 20, 64))
    draw.text((292, 219), f"Active runners: {active}", fill=TEXT_SEC, font=font_sm)

    # === Arrow: GitHub → Control Plane ===
    arrow_progress = (cycle % 10) / 10.0
    draw_arrow(draw, 220, 150, 270, 150, PURPLE, arrow_progress)
    draw.text((230, 135), "webhook", fill=TEXT_DIM, font=font_sm)

    # === RIGHT: Compute Resources ===
    draw_box(draw, 520, 50, 360, 200, fill=None, border=BORDER)
    draw.text((540, 58), "YOUR VPC — PRIVATE SUBNETS", fill=TEXT_DIM, font=font_sm)

    # Three compute backends
    backends = [
        {"name": "EC2", "y": 80, "color": BLUE, "detail": "m7i.2xlarge"},
        {"name": "ECS", "y": 130, "color": GREEN, "detail": "2 vCPU / 4GB"},
        {"name": "EKS", "y": 180, "color": YELLOW, "detail": "pod/runner-x"},
    ]

    for i, b in enumerate(backends):
        # Highlight active backend
        is_active = b["name"] == current_job["backend"]
        box_border = b["color"] if is_active else BORDER

        draw_box(draw, 535, b["y"], 155, 40, fill=CARD, border=box_border)
        draw.text((548, b["y"] + 5), b["name"], fill=TEXT if is_active else TEXT_SEC, font=font_md)
        draw.text((548, b["y"] + 22), b["detail"], fill=TEXT_DIM, font=font_sm)

        # Runner dots (active runners)
        if is_active:
            num_dots = 1 + (frame_num % 3)
            for d in range(num_dots):
                dx = 700 + d * 22
                pulse_offset = ((frame_num + d * 3) % 8) / 8.0
                dot_r = int(5 + pulse_offset * 2)
                draw.ellipse((dx - dot_r, b["y"] + 12 - dot_r, dx + dot_r, b["y"] + 12 + dot_r), fill=b["color"])
            # "ephemeral" label
            draw.text((697, b["y"] + 26), "ephemeral", fill=TEXT_DIM, font=font_sm)
        else:
            # Idle dots
            for d in range(2):
                dx = 700 + d * 22
                draw.ellipse((dx - 3, b["y"] + 14, dx + 3, b["y"] + 20), fill=TEXT_DIM)

    # === Arrow: Control Plane → Compute ===
    arrow_progress2 = ((cycle + 5) % 10) / 10.0
    draw_arrow(draw, 470, 150, 535, 150, GREEN, arrow_progress2)
    draw.text((478, 135), "provision", fill=TEXT_DIM, font=font_sm)

    # === BOTTOM: IR Cache ===
    draw_box(draw, 270, 280, 360, 90, fill=SURFACE)
    draw.text((290, 288), "iR CACHE SERVICE", fill=TEXT_DIM, font=font_sm)

    # Cache activity
    draw_box(draw, 282, 308, 160, 50, fill=(26, 20, 64))
    draw.text((292, 314), "S3 Cache", fill=GREEN, font=font_md)

    # Cache hit/miss animation
    cache_cycle = frame_num % 30
    if cache_cycle < 15:
        draw.text((292, 332), "● HIT  restore 2.1s", fill=GREEN, font=font_sm)
    else:
        draw.text((292, 332), "● SAVE 847MB multipart", fill=BLUE, font=font_sm)

    # Docker cache
    draw_box(draw, 452, 308, 160, 50, fill=(26, 20, 64))
    draw.text((462, 314), "Docker Layers", fill=PURPLE, font=font_md)

    layer_count = 12 + (frame_num % 5)
    draw.text((462, 332), f"● {layer_count} layers cached", fill=TEXT_SEC, font=font_sm)

    # Arrow: Compute → Cache (bidirectional)
    cache_arrow_t = (cycle % 8) / 8.0
    # Down arrow from compute
    mid_x = 450
    draw_arrow(draw, mid_x, 250, mid_x, 280, GREEN, cache_arrow_t)
    # Up arrow to compute
    draw_arrow(draw, mid_x + 40, 280, mid_x + 40, 250, BLUE, 1.0 - cache_arrow_t)
    draw.text((mid_x + 50, 258), "save/restore", fill=TEXT_DIM, font=font_sm)

    # === BOTTOM: Lifecycle indicator ===
    draw_box(draw, 20, 390, 200, 90, fill=SURFACE)
    draw.text((40, 398), "LIFECYCLE", fill=TEXT_DIM, font=font_sm)

    # Rotating lifecycle stages
    stages = ["Queued", "Matched", "Provisioned", "Running", "Completed", "Destroyed"]
    stage_idx = (frame_num // 4) % len(stages)

    for i, stage in enumerate(stages):
        y_s = 416 + i * 11
        if i == stage_idx:
            draw.text((40, y_s), f"▶ {stage}", fill=GREEN, font=font_sm)
        elif i < stage_idx:
            draw.text((40, y_s), f"✓ {stage}", fill=TEXT_DIM, font=font_sm)
        else:
            draw.text((40, y_s), f"  {stage}", fill=TEXT_DIM, font=font_sm)

    # === Stats counter ===
    draw_box(draw, 650, 280, 210, 90, fill=SURFACE)
    draw.text((670, 288), "STATS", fill=TEXT_DIM, font=font_sm)

    jobs_completed = 1247 + frame_num
    draw.text((670, 308), f"Jobs today: {jobs_completed}", fill=TEXT, font=font_md)
    draw.text((670, 328), f"Avg duration: 2m 14s", fill=TEXT_SEC, font=font_sm)
    draw.text((670, 345), f"Cost saved: 78.6%", fill=GREEN, font=font_sm)

    return img


# Generate frames
frames = []
for i in range(FRAMES):
    frames.append(generate_frame(i))

# Save as animated GIF
output_path = "/Users/spahuja/github/harness-ci/ir/www/docs/images/how-it-works.gif"
frames[0].save(
    output_path,
    save_all=True,
    append_images=frames[1:],
    duration=DURATION,
    loop=0,
    optimize=True,
)

print(f"Generated {output_path} ({len(frames)} frames, {os.path.getsize(output_path) / 1024:.0f}KB)")
