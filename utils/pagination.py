from math import ceil


def paginate_queryset(queryset, page=1, items_per_page=10):
    page = max(int(page), 1)
    items_per_page = max(int(items_per_page), 1)

    total_items = queryset.count()
    total_pages = max(1, ceil(total_items / items_per_page))

    page = min(page, total_pages)
    start = (page - 1) * items_per_page
    end = start + items_per_page

    return {
        "items": queryset[start:end],
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
    }
