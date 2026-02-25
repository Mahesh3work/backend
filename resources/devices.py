from flask import make_response, jsonify, request, Response
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
import time
import mysql.connector

from db import db
from schemas import DeviceSchema, DeviceConfigSchema, ProductionPlanSchema,deviceadd

blp = Blueprint("Devices", __name__, description="Operations on devices", url_prefix="/api")


@blp.route("/devices")
class Device(MethodView):
    @jwt_required(locations=["cookies", "headers"])
    @blp.response(200)
    def get(self):
        user_id = get_jwt_identity()
        devices = db.get_all_devices(user_id)
        return devices

    @blp.arguments(DeviceSchema)
    @jwt_required(locations=["cookies", "headers"], fresh=True)
    @blp.response(201, DeviceSchema)
    def post(self, device_data, site_id):
        user_id = get_jwt_identity()
        device_id = db.add_device(device_name=device_data['device_name'], device_url=device_data['device_url'], site_id=site_id, user_id=user_id)
        device_data['device_id'] = device_id
        return device_data
    
@blp.route('/<int:device_id>/download-device-logs')
class DownloadDeviceLogs(MethodView):

    def get(self, device_id):
        try:
            # Fetch the device URL from the database
            device_url = db.get_device_url_by_device_id(device_id)
            # Extract query parameters (instead of using request.get_json())
            file_format = request.args.get("format", "csv")
            days = request.args.get("days", 30)
            cumulative = request.args.get("cumulative")

            if not device_url:
                return jsonify({
                    "status": "error",
                    "device_id": device_id,
                    "message": "Device URL not found"
                }), 404

            # Ensure proper URL formatting
            full_url = f"https://{device_url}/download-csv?format={file_format}&days={days}&cumulative={cumulative}"

            # Fetch log file from the device
            response = requests.get(full_url, timeout=5)
            response.raise_for_status()

            # Stream the response back to the client
            return Response(
                response.content,
                content_type=response.headers.get("Content-Type", "application/octet-stream"),
                headers={
                    "Content-Disposition": response.headers.get("Content-Disposition", f'attachment; filename="logs.{file_format}"')
                },
                status=response.status_code
            )

        except requests.exceptions.Timeout:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": "Request timed out"
            }), 504  

        except requests.exceptions.ConnectionError:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": "Failed to connect to the device"
            }), 502  

        except requests.exceptions.RequestException as e:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": "something went wrong. Please ensure query parameter 'fromat=csv or json or json-file'"
            }), 500  

@blp.route('/<int:device_id>/get-device-parts')
class GetDeviceParts(MethodView):

    @blp.response(200)
    def get(self, device_id):
        try:
            device_url = db.get_device_url_by_device_id(device_id)
            
            if not device_url:
                return jsonify({
                    "status": "error",
                    "device_id": device_id,
                    "message": "Device URL not found"
                }), 404

            response = requests.get(
                url=f"https://{device_url}/get-data", 
                timeout=5  # Set timeout to 5 seconds to avoid blocking
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": "Request timed out"
            }), 504  # Gateway Timeout

        except requests.exceptions.ConnectionError:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": "Failed to connect to the device"
            }), 502  # Bad Gateway

        except requests.exceptions.RequestException as e:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": str(e)
            }), 500


@blp.route('/<int:device_id>/stream-device-data')
class StreamDeviceData(MethodView):

    @blp.response(200)
    def get(self, device_id):
        try:
            device_url = db.get_device_url_by_device_id(device_id)
            
            if not device_url:
                return jsonify({
                    "status": "error",
                    "device_id": device_id,
                    "message": "Device URL not found"
                }), 404

            response = requests.get(
                url=f"{device_url}/get-data/0", 
                timeout=5  # Set timeout to 5 seconds to avoid blocking
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": "Request timed out"
            }), 504  # Gateway Timeout

        except requests.exceptions.ConnectionError:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": "Failed to connect to the device"
            }), 502  # Bad Gateway

        except requests.exceptions.RequestException as e:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": str(e)
            }), 500

@blp.route("/<int:device_id>/device-config")
class ConfigureDevice(MethodView):

    @blp.arguments(DeviceConfigSchema)  # DeviceConfigSchema should define expected request body
    @blp.response(200, description="Data successfully fetched from the device")
    @blp.response(400, description="Invalid request data")
    @blp.response(500, description="Internal server error")
    def post(self, device_data, device_id):
        """
        Fetches data from a specified device.

        Parameters:
            device_data (dict): The request body containing the data to send to the device.
            device_id (str): The unique identifier of the target device.

        Returns:
            JSON Response with device data or an error message.
        """
        try:
            # Fetch the device URL from the database
            payload = dict(request.get_json())
            device_url = db.get_device_url_by_device_id(device_id)
            function_code = payload.get('function_code')

            if not device_url:
                return jsonify({
                    "status": "error",
                    "message": f"Device with ID {device_id} not found"
                }), 400

            # Send request to the device
            if function_code == "update-target":
                response = requests.post(
                    url=f"https://{device_url}/update-target/{device_data['location_id']}",
                    json=device_data  # Send as JSON
                )
            elif function_code == "set-last-used": 
                response = requests.post(
                    url=f"https://{device_url}/set-last-used/{device_data['location_id']}",
                    json=device_data  # Send as JSON
                )

            response.raise_for_status()  # Raises error for 4xx/5xx status codes

            return jsonify({
                "status": "success",
                "device_response": response.json()
            }), 200

        except requests.exceptions.ConnectionError:
            return jsonify({
                "status": "error",
                "message": f"Failed to connect to device {device_id}."
            }), 500
        except requests.exceptions.Timeout:
            return jsonify({
                "status": "error",
                "message": f"Request to device {device_id} timed out."
            }), 500
        except requests.exceptions.HTTPError as e:
            return jsonify({
                "status": "error",
                "message": f"HTTP Error: {e.response.status_code} - {e.response.reason}"
            }), e.response.status_code
        except requests.exceptions.RequestException as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

@blp.route("/<int:device_id>/production-plan")
class ProductionPlan(MethodView):

    def get(self, device_id):
        try:
            device_url = db.get_device_url_by_device_id(device_id)
            
            if not device_url:
                return jsonify({
                    "status": "error",
                    "device_id": device_id,
                    "message": "Device URL not found"
                }), 404

            response = requests.get(
                url=f"https://{device_url}/production-plan", 
                timeout=10  # Set timeout to 5 seconds to avoid blocking
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": "Request timed out"
            }), 504  # Gateway Timeout

        except requests.exceptions.ConnectionError:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": "Failed to connect to the device"
            }), 502  # Bad Gateway

        except requests.exceptions.RequestException as e:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": str(e)
            }), 500
        
    @blp.arguments(ProductionPlanSchema)
    def post(self, prod_plan, device_id):
        try:
            device_url = db.get_device_url_by_device_id(device_id)
            
            if not device_url:
                return jsonify({
                    "status": "error",
                    "device_id": device_id,
                    "message": "Device URL not found"
                }), 404

            response = requests.post(
                    url=f"https://{device_url}/production-plan",
                    json=prod_plan  
                )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": "Request timed out"
            }), 504  # Gateway Timeout

        except requests.exceptions.ConnectionError:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": "Failed to connect to the device"
            }), 502  # Bad Gateway

        except requests.exceptions.RequestException as e:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": str(e)
            }), 500
        except Exception as e:
            return jsonify({
                "status": "error",
                "device_id": device_id,
                "message": str(e)
            }), 500
        
@blp.route("/device")
class Device(MethodView):

    @jwt_required(locations=["cookies", "headers"])
    @blp.response(200)
    def get(self):
        id = get_jwt_identity()
        devices = db.get_all_devices_by_user(id)
        return jsonify({"devices": devices}, 200)

    @blp.arguments(deviceadd)
    @jwt_required(locations=["cookies", "headers"])
    @blp.response(201, deviceadd)
    def post(self, device_data):
        user_id = get_jwt_identity()
        device_id = db.add_device(device_name=device_data['device_name'], device_url=device_data['device_url'], site_id=device_data['site_id'], user_id=user_id)
        device_data['device_id'] = device_id
        return device_data
    
    @blp.arguments(deviceadd)
    @jwt_required(locations=["cookies", "headers"])
    @blp.response(201, deviceadd)
    def put(self, device_data):
        user_id = get_jwt_identity()
        device_id = db.add_device_by_user(device_name=device_data['device_name'], device_url=device_data['device_url'], site_id=device_data['site_id'], user_id=user_id)
        device_data['device_id'] = device_id
        return device_data
    
@blp.route("/device/<int:device_id>")
class DeviceById(MethodView):

    @jwt_required(locations=["cookies", "headers"])
    def delete(self, device_id):
        user_id = get_jwt_identity()
        db.delete_device_by_user(device_id=device_id, user_id=user_id)
        return {"message": "Device deleted successfully"}, 200


@blp.route("/adddevice", methods=["POST"])
@jwt_required(locations=["cookies", "headers"])
def add_device():

    try:
        data = request.json
        user_id = get_jwt_identity()

        result = db.add_device(
            data["designInfo"],
            data["salesInfo"],
            data["productionInfo"],
            user_id,
            data["site_id"],
            data["expiry_date"]
        )

        return jsonify({
            "success": True,
            "data": result
        }), 201

    except mysql.connector.Error as e:   # DB error
        return jsonify({
            "success": False,
            "error": "Database error",
            "details": str(e)
        }), 500

    except KeyError as e:  # missing JSON field
        return jsonify({
            "success": False,
            "error": f"Missing field: {str(e)}"
        }), 400

    except Exception as e:  # unexpected error
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500

@blp.route("/devices/<int:device_id>", methods=["GET"])
@jwt_required(locations=["cookies", "headers"])
def get_device(device_id):
    user_id = get_jwt_identity()
    result = db.get_device(user_id,device_id)

    if not result:
        return jsonify({"message": "Device not found"}), 404

    return jsonify(result)

# @blp.route("/devices/<int:device_id>", methods=["PUT"])
# def update_device(device_id):

#     data = request.json

#     result = db.update_device(
#         device_id,
#         data["designInfo"],
#         data["salesInfo"],
#         data["productionInfo"],
#         data["expiry_date"]
#     )

#     return jsonify(result)

@blp.route("/devices/<int:device_id>", methods=["PUT"])
@jwt_required(locations=["cookies", "headers"])
def update_device(device_id):

    try:
        data = request.json
        user_id = get_jwt_identity()
        print("Incoming payload:", data)
        design_info = data.get("designInfo", {})
        sales_info = data.get("salesInfo", {})
        production_info = data.get("productionInfo", {})
        expiry_date = data.get("expiry_date")
        site_id = data.get("site_id")
        result = db.update_device(
            device_id,
            design_info,
            sales_info,
            production_info,
            expiry_date,
            site_id,
            user_id
        )

        return jsonify(result), 200

    except KeyError as e:
        print("Missing key error:", e)
        return jsonify({
            "error": f"Missing required field: {str(e)}"
        }), 400

    except Exception as e:
        print("Unexpected error:", e)
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500


# @blp.route("/devices", methods=["GET"])
# def get_all_devices():

#     result = db.get_all_devices()

#     return jsonify(result)

@blp.route("/devices/<int:device_id>", methods=["DELETE"])
@jwt_required(locations=["cookies", "headers"])
def delete_device_api(device_id):
    user_id = get_jwt_identity()
    response = db.delete_device(user_id,device_id)
    return jsonify(response)
