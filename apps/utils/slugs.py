from django.utils.text import slugify

from apps.models.restaurants import Restaurant


def unique_restaurant_slug(
    name: str,
    *,
    preferred: str | None = None,
    exclude_pk: int | None = None,
) -> str:
    """
    Restoran uchun unique slug yasaydi.
    - preferred berilgan va bo'sh bo'lmasa undan foydalanadi
    - aks holda name dan slugify
    - collision bo'lsa -2, -3, ... qo'shadi
    """
    raw = (preferred or "").strip() or name
    base = slugify(raw, allow_unicode=True) or slugify(name, allow_unicode=True) or "restaurant"
    base = base[:200]
    slug = base
    n = 2
    qs = Restaurant.objects.all()
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    while qs.filter(slug=slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug
