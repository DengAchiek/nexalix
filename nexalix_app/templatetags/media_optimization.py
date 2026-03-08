from django import template

register = template.Library()

_PRESETS = {
    "brand": "f_auto,q_auto,dpr_auto,w_360,c_limit",
    "card": "f_auto,q_auto,dpr_auto,w_720,c_limit",
    "thumb": "f_auto,q_auto,dpr_auto,w_220,h_220,c_fill",
    "hero_poster": "f_auto,q_auto,dpr_auto,w_1920,c_limit",
    "case_detail": "f_auto,q_auto,dpr_auto,w_1280,c_limit",
    "video": "f_auto,q_auto,vc_auto",
}


def _with_cloudinary_transform(url, transform):
    if not url or "res.cloudinary.com" not in url or "/upload/" not in url:
        return url
    return url.replace("/upload/", f"/upload/{transform}/", 1)


@register.filter(name="optimized_media")
def optimized_media(url, preset="card"):
    transform = _PRESETS.get((preset or "card").strip(), _PRESETS["card"])
    return _with_cloudinary_transform(url, transform)
