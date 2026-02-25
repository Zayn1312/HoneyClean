"""
HoneyClean – Image processing operations
"""

from PIL import Image, ImageDraw, ImageFilter
from core.config import PLATFORM_PRESETS


def generate_shadow(fg_img, shadow_type="drop", opacity=0.6, blur_radius=20, offset=(8, 12)):
    if shadow_type == "none" or not fg_img:
        return fg_img
    alpha = fg_img.split()[3]
    w, h = fg_img.size
    if shadow_type == "contact":
        offset, blur_radius = (0, h // 8), 15
    elif shadow_type == "float":
        offset, blur_radius = (0, h // 6), 30
    shadow_mask = alpha.filter(ImageFilter.GaussianBlur(blur_radius))
    shadow_color = Image.new("RGBA", (w, h), (0, 0, 0, int(255 * opacity)))
    shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow_layer.paste(shadow_color, mask=shadow_mask)
    pad = max(abs(offset[0]), abs(offset[1])) + blur_radius
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    canvas.paste(shadow_layer, (pad + offset[0], pad + offset[1]), shadow_layer)
    canvas.paste(fg_img, (pad, pad), fg_img)
    return canvas


def decontaminate_edges(img, strength=0.5):
    try:
        import numpy as np
        arr = np.array(img, dtype=np.float32)
        if arr.shape[2] < 4: return img
        rgb, alpha = arr[:, :, :3], arr[:, :, 3:4] / 255.0
        opaque = alpha[:, :, 0] > 0.9
        if opaque.sum() == 0: return img
        avg = rgb[opaque].mean(axis=0)
        semi = (alpha[:, :, 0] > 0.05) & (alpha[:, :, 0] < 0.9)
        blend = (1.0 - alpha[semi]) * strength
        rgb[semi] = rgb[semi] * (1 - blend[:, np.newaxis]) + avg * blend[:, np.newaxis]
        out = np.concatenate([np.clip(rgb, 0, 255), arr[:, :, 3:4]], axis=2).astype(np.uint8)
        return Image.fromarray(out)
    except Exception:
        return img


def apply_edge_feather(img, radius):
    if radius <= 0: return img
    alpha = img.split()[3]
    result = img.copy()
    result.putalpha(alpha.filter(ImageFilter.GaussianBlur(radius)))
    return result


def apply_platform_preset(result_img, preset):
    bbox = result_img.split()[3].getbbox()
    if not bbox: return result_img
    subject = result_img.crop(bbox)
    tw, th = preset["size"]
    pad = preset["padding_pct"]
    mw, mh = int(tw * (1 - 2 * pad)), int(th * (1 - 2 * pad))
    subject.thumbnail((mw, mh), Image.LANCZOS)
    if preset["bg"]:
        canvas = Image.new("RGB", (tw, th), preset["bg"])
        canvas.paste(subject, ((tw - subject.width) // 2, (th - subject.height) // 2), subject.split()[3])
    else:
        canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        canvas.paste(subject, ((tw - subject.width) // 2, (th - subject.height) // 2))
    return canvas


def replace_background(fg_img, bg_type, bg_value=None):
    if bg_type == "transparent": return fg_img
    w, h = fg_img.size
    if bg_type == "white":
        bg = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    elif bg_type == "color" and bg_value:
        bg = Image.new("RGBA", (w, h), (*bg_value, 255))
    elif bg_type == "image" and bg_value:
        bg = bg_value.resize((w, h), Image.LANCZOS).convert("RGBA")
    else:
        return fg_img
    canvas = Image.new("RGBA", (w, h))
    canvas.paste(bg, (0, 0))
    canvas.paste(fg_img, (0, 0), fg_img.split()[3])
    return canvas


def _make_checker(w, h, sq=12):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(0, h, sq):
        for x in range(0, w, sq):
            c = (200, 200, 200) if (x // sq + y // sq) % 2 == 0 else (150, 150, 150)
            d.rectangle([x, y, x + sq - 1, y + sq - 1], fill=c)
    return img
