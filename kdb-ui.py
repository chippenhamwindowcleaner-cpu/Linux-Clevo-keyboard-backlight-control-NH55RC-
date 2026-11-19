#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import colorsys
import json

LED_PATH = "/sys/class/leds/rgb:kbd_backlight/"
SAVE_FILE = os.path.expanduser("~/.kbd_saved_colors.json")

current_hue = 0.66
current_sat = 1.0
current_val = 1.0
current_rgb = [0, 0, 255]
saved_colors = []
update_timer = None

if os.path.exists(SAVE_FILE):
    try:
        with open(SAVE_FILE, "r") as f:
            saved_colors = json.load(f)
    except:
        saved_colors = []

def run_cmd(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def ensure_driver():
    if not os.path.exists(LED_PATH):
        run_cmd("modprobe tuxedo_keyboard")
        run_cmd("modprobe clevo_wmi")
        run_cmd("modprobe clevo_acpi")

def hardware_set_color(r, g, b):
    ensure_driver()
    # Clevo GRB swap
    run_cmd(f"echo {g} {r} {b} > {LED_PATH}multi_intensity")
    run_cmd(f"echo 255 > {LED_PATH}brightness")

def commit_to_hardware(r, g, b):
    global update_timer
    if update_timer:
        root.after_cancel(update_timer)
    update_timer = root.after(50, hardware_set_color, r, g, b)

# --- CUSTOM GRADIENT SLIDERS ---
def draw_gradient(canvas, param_type):
    canvas.delete("gradient")
    width = 250
    height = 20
    for x in range(width):
        if param_type == 'hue':
            r, g, b = colorsys.hsv_to_rgb(x/width, 1, 1)
        elif param_type == 'sat':
            r, g, b = colorsys.hsv_to_rgb(current_hue, x/width, current_val)
        elif param_type == 'val':
            r, g, b = colorsys.hsv_to_rgb(current_hue, current_sat, x/width)
            
        c_hex = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        canvas.create_line(x, 0, x, height, fill=c_hex, tags="gradient")
    
    # Draw the drag thumb
    draw_thumb(canvas, param_type)

def draw_thumb(canvas, param_type):
    width = 250
    if param_type == 'hue': val = current_hue
    elif param_type == 'sat': val = current_sat
    elif param_type == 'val': val = current_val
    
    thumb_tag = f"thumb_{param_type}"
    canvas.delete(thumb_tag)
    x = int(val * width)
    canvas.create_oval(x - 6, -2, x + 6, 22, outline="white", width=2, fill="", tags=thumb_tag)

def on_drag(event, param_type, canvas):
    global current_hue, current_sat, current_val
    width = 250
    x = max(0, min(event.x, width))
    val = x / width
    
    if param_type == 'hue':
        current_hue = val
        draw_thumb(hue_canvas, 'hue')
        draw_gradient(sat_canvas, 'sat')
        draw_gradient(val_canvas, 'val')
    elif param_type == 'sat':
        current_sat = val
        draw_thumb(sat_canvas, 'sat')
        draw_gradient(val_canvas, 'val')
    elif param_type == 'val':
        current_val = val
        draw_thumb(val_canvas, 'val')
        draw_gradient(sat_canvas, 'sat')
        
    update_color_from_sliders()

def on_mouse_release(event):
    hardware_set_color(*current_rgb)

def update_color_from_sliders():
    global current_rgb
    r, g, b = colorsys.hsv_to_rgb(current_hue, current_sat, current_val)
    current_rgb = [int(r * 255), int(g * 255), int(b * 255)]
    hex_color = f"#{current_rgb[0]:02x}{current_rgb[1]:02x}{current_rgb[2]:02x}"
    preview_box.config(bg=hex_color)
    status_label.config(text=f"Custom: RGB({current_rgb[0]}, {current_rgb[1]}, {current_rgb[2]})")
    commit_to_hardware(*current_rgb)

def turn_off():
    hardware_set_color(0, 0, 0)
    status_label.config(text="Status: OFF (Dark)", fg="gray")
    preview_box.config(bg="#000000")

def apply_saved_color(rgb):
    global current_rgb
    current_rgb = rgb
    hardware_set_color(*current_rgb)
    hex_color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    preview_box.config(bg=hex_color)
    status_label.config(text=f"Applied Saved RGB: {rgb}", fg="green")

def save_current_color():
    if current_rgb not in saved_colors:
        saved_colors.append(current_rgb)
        with open(SAVE_FILE, "w") as f:
            json.dump(saved_colors, f)
        redraw_saved_colors()
        messagebox.showinfo("Saved", "Color saved to your palette!")

def redraw_saved_colors():
    for widget in saved_frame.winfo_children():
        widget.destroy()
    for idx, rgb in enumerate(saved_colors):
        hex_c = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        btn = tk.Button(saved_frame, bg=hex_c, width=3, height=1, command=lambda r=rgb: apply_saved_color(r))
        btn.grid(row=idx // 8, column=idx % 8, padx=2, pady=2)

# --- UI SETUP ---
root = tk.Tk()
root.title("Clevo Keyboard Control")
root.geometry("400x650")
root.configure(padx=20, pady=15)

tk.Label(root, text="Keyboard Backlight", font=("Helvetica", 16, "bold")).pack(pady=5)
status_label = tk.Label(root, text="Status: Ready", fg="blue")
status_label.pack(pady=5)

tk.Button(root, text="TURN OFF", font=("Helvetica", 12, "bold"), bg="#ffcccc", command=turn_off).pack(pady=10, fill="x")

custom_frame = tk.LabelFrame(root, text="Custom Color", padx=10, pady=10)
custom_frame.pack(fill="x", pady=5)

preview_box = tk.Label(custom_frame, width=6, height=2, bg="#0000ff", relief="sunken")
preview_box.grid(row=0, column=0, rowspan=3, padx=10)

# HUE
tk.Label(custom_frame, text="Hue").grid(row=0, column=1, sticky="w")
hue_canvas = tk.Canvas(custom_frame, width=250, height=20, highlightthickness=0, cursor="hand2")
hue_canvas.grid(row=0, column=2, pady=5)
hue_canvas.bind("<Button-1>", lambda e: on_drag(e, 'hue', hue_canvas))
hue_canvas.bind("<B1-Motion>", lambda e: on_drag(e, 'hue', hue_canvas))
hue_canvas.bind("<ButtonRelease-1>", on_mouse_release)

# SATURATION
tk.Label(custom_frame, text="Sat").grid(row=1, column=1, sticky="w")
sat_canvas = tk.Canvas(custom_frame, width=250, height=20, highlightthickness=0, cursor="hand2")
sat_canvas.grid(row=1, column=2, pady=5)
sat_canvas.bind("<Button-1>", lambda e: on_drag(e, 'sat', sat_canvas))
sat_canvas.bind("<B1-Motion>", lambda e: on_drag(e, 'sat', sat_canvas))
sat_canvas.bind("<ButtonRelease-1>", on_mouse_release)

# VALUE
tk.Label(custom_frame, text="Val").grid(row=2, column=1, sticky="w")
val_canvas = tk.Canvas(custom_frame, width=250, height=20, highlightthickness=0, cursor="hand2")
val_canvas.grid(row=2, column=2, pady=5)
val_canvas.bind("<Button-1>", lambda e: on_drag(e, 'val', val_canvas))
val_canvas.bind("<B1-Motion>", lambda e: on_drag(e, 'val', val_canvas))
val_canvas.bind("<ButtonRelease-1>", on_mouse_release)

tk.Button(custom_frame, text="Save Current Color", command=save_current_color, bg="#d4edda").grid(row=3, column=0, columnspan=3, pady=10, sticky="ew")

saved_frame_outer = tk.LabelFrame(root, text="Saved Palette", padx=10, pady=10)
saved_frame_outer.pack(fill="x", pady=5)
saved_frame = tk.Frame(saved_frame_outer)
saved_frame.pack()

preset_frame = tk.LabelFrame(root, text="Quick Presets", padx=10, pady=10)
preset_frame.pack(fill="x", pady=5)
tk.Button(preset_frame, text="Pastel Pink", bg="#ffb6c1", command=lambda: apply_saved_color([255, 150, 200])).grid(row=0, column=0, padx=5)
tk.Button(preset_frame, text="White", bg="#ffffff", command=lambda: apply_saved_color([150, 255, 255])).grid(row=0, column=1, padx=5)
tk.Button(preset_frame, text="Red", bg="#ff0000", fg="white", command=lambda: apply_saved_color([255, 0, 0])).grid(row=0, column=2, padx=5)

# Draw initial gradients
draw_gradient(hue_canvas, 'hue')
draw_gradient(sat_canvas, 'sat')
draw_gradient(val_canvas, 'val')
redraw_saved_colors()

tk.Label(root, text="Note: Requires administrator privileges to run.", font=("Helvetica", 8), fg="gray").pack(side="bottom", pady=10)

root.mainloop()
