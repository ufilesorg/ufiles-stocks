from .models import Imagination


async def get_status_for_imagination(imagination: Imagination):
    status = {
        "id": imagination.id,
        "status": imagination.status,
        "created_at": imagination.created_at,
        "updated_at": imagination.updated_at,
    }
    return status
