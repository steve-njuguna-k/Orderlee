from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from oauth2_provider.contrib.rest_framework import TokenHasScope
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import Item
from .serializers import ItemSerializer


class ItemAPIView(APIView):
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated, TokenHasScope]
    required_scopes = ["openid"]

    def post(self, request):
        """POST request function to create a new Item object"""
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return JsonResponse(
                    {
                        "status": status.HTTP_201_CREATED,
                        "message": "Item Created Successfully!",
                        "results": serializer.data,
                    }
                )
        except Exception as e:
            return JsonResponse(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "An Error Occurred!",
                    "results": {"error": str(e)},
                }
            )

    def get(self, request, pk=None):
        ("""GET request function to either retrieve a given Item"
            "object or list all Items objects""")
        if pk:
            try:
                item_obj = get_object_or_404(Item, id=pk)
                serializer = self.serializer_class(item_obj)
                return JsonResponse(
                    {
                        "status": status.HTTP_200_OK,
                        "message": "Item Details Retrieved Successfully!",
                        "results": serializer.data,
                    }
                )
            except Exception as e:
                return JsonResponse(
                    {
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "An Error Occurred!",
                        "results": {"error": str(e)},
                    }
                )
        else:
            try:
                item_objs = Item.objects.all().order_by("-date_created")
                serializer = self.serializer_class(
                    item_objs, many=True, context={"request": request}
                )
                return JsonResponse(
                    {
                        "status": status.HTTP_200_OK,
                        "message": "Items Retrieved Successfully!",
                        "results": serializer.data,
                    }
                )
            except Exception as e:
                return JsonResponse(
                    {
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "An Error Occurred!",
                        "results": {"error": str(e)},
                    }
                )

    def patch(self, request, pk=None):
        """PATCH request function to update a given Item object"""
        try:
            item_obj = get_object_or_404(Item, id=pk)
            serializer = self.serializer_class(
                instance=item_obj, data=request.data, partial=True
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return JsonResponse(
                    {
                        "status": status.HTTP_200_OK,
                        "message": "Item Details Updated Successfully!",
                        "results": serializer.data,
                    }
                )
        except Exception as e:
            return JsonResponse(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "An Error Occurred!",
                    "results": {"error": str(e)},
                }
            )

    def delete(self, request, pk=None):
        """DELETE request function to delete a given Item object"""
        try:
            item_obj = get_object_or_404(Item, id=pk)
            item_obj.delete()
            return JsonResponse(
                {
                    "status": status.HTTP_204_NO_CONTENT,
                    "message": "Item Details Deleted Successfully!",
                }
            )
        except Exception as e:
            return JsonResponse(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "An Error Occurred!",
                    "results": {"error": str(e)},
                }
            )
