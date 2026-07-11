"""
Object-level permissions — the principle of least privilege.
Every view that touches a resource checks ownership here.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsFarmOwner(BasePermission):
    """
    Allow access only if the authenticated user owns the farm
    associated with the object being accessed.
    Works for: Farm, Season, Buyer, Worker
    """
    message = "You do not own this farm."

    def has_object_permission(self, request, view, obj):
        # obj could be Farm directly, or something with a .farm FK
        farm = obj if hasattr(obj, "owner") else getattr(obj, "farm", None)
        if farm is None:
            return False
        return farm.owner == request.user


class IsPlantingOwner(BasePermission):
    """
    For objects hanging off PlantingRecord (expenses, harvests, labour).
    Walks: obj → planting_record → season → farm → owner
    """
    message = "You do not own the farm this planting belongs to."

    def has_object_permission(self, request, view, obj):
        planting = getattr(obj, "planting_record", obj)
        return planting.season.farm.owner == request.user
