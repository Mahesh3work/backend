import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
import os
import json
# import psycopg2
# from psycopg2 import pool, extras

# Load environment variables
load_dotenv()

# Pool size per process. Total MySQL connections ≈ (gunicorn workers × DB_POOL_SIZE).
# Keep total under MySQL max_connections (e.g. SHOW VARIABLES LIKE 'max_connections';).
POOL_SIZE = min(int(os.getenv("DB_POOL_SIZE", "5")), 20)

class DatabaseAccess:
    def __init__(self):
        self.database_uri = {
            'host':  os.getenv("DB_HOST",''),
            'user':  os.getenv("DB_USER"),
            'password': os.getenv("DB_PASSWORD"),
            'database': os.getenv("DB_NAME"),
            'port': int(os.getenv("DB_PORT", 3306)),
            "use_pure": True,
        }

        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=POOL_SIZE,
            pool_reset_session=True,
            **self.database_uri
        )
        # self.pool = psycopg2.pool.SimpleConnectionPool(
        #     minconn=1,
        #     maxconn=10,
        #     **self.database_uri
        # )

    def _get_connection(self):
        return self.pool.get_connection()

    def _execute_query(self, query, params=None, fetchone=False, fetchall=False):
        conn = self._get_connection()
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            try:
                cursor.execute(query, params)
                result = None
                if fetchone:
                    result = cursor.fetchone()
                elif fetchall:
                    result = cursor.fetchall()
                # Drain any extra result sets (e.g. from CALL) so connection is safe to return
                while cursor.nextset():
                    pass
                conn.commit()
                return result
            except Exception as e:
                print(f"Database query error: {e}")
                conn.rollback()
                raise
            finally:
                cursor.close()
        finally:
            conn.close()  # always return connection to pool

    def _with_connection(self):
        """Context manager: get a connection from the pool and always return it."""
        conn = self._get_connection()
        try:
            yield conn
        finally:
            conn.close()

    # def _execute_procedure(self, proc_name, params=()):
    #     conn = self._get_connection()
    #     cursor = conn.cursor(dictionary=True)

    #     try:
    #         cursor.callproc(proc_name, params)

    #         result = None

    #         # Read stored procedure result sets
    #         for res in cursor.stored_results():
    #             result = res.fetchall()

    #         conn.commit()
    #         return result

    #     except Exception as e:
    #         print(f"Procedure error: {e}")
    #         conn.rollback()
    #         raise

    #     finally:
    #         cursor.close()
    #         conn.close()
        
    def _execute_procedure(self, proc_name, params=()):
        conn = self._get_connection()
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            try:
                cursor.callproc(proc_name, params)
                results = []
                for result in cursor.stored_results():
                    rows = result.fetchall()
                    if rows:
                        results.extend(rows)
                    result.close()
                # Drain any remaining result sets so connection can be safely returned to pool
                while cursor.nextset():
                    pass
                conn.commit()
                return results
            except Exception as e:
                print(f"Procedure error: {e}")
                conn.rollback()
                raise
            finally:
                cursor.close()
        finally:
            conn.close()  # always return connection to pool


    # ------------------------- Users Table Operations -------------------------

    def is_user_already_exists(self, name: str) -> bool:
        query = "SELECT 1 FROM user WHERE name = %s"
        return self._execute_query(query, (name,), fetchone=True) is not None

    # def get_user_by_username(self, username: str):
    #     query = "SELECT * FROM users_login_details WHERE username = %s"
    #     data = self._execute_query(query, (username,), fetchone=True)
    #     if data:
    #         return {
    #             "user_id": data["user_id"],
    #             "username": data["username"],
    #             "password": data["password_hash"]
    #         }
    #     return None
    def get_user_by_username(self, name: str):
        query = """
            SELECT 
                u.id,
                u.name,
                u.password,
                u.role_id,
                r.role_name,
                u.orgid,
                u.clientid
            FROM user u
            JOIN role r ON r.id = u.role_id
            WHERE u.name = %s
        """
        data = self._execute_query(query, (name,), fetchone=True)

        if data:
            return {
                "user_id": data["id"],
                "username": data["name"],
                "password": data["password"],
                "role_id": data["role_id"],
                "role_name": data["role_name"],
                "orgid": data["orgid"],
                "clientid": data["clientid"]
            }
        return None


    def get_user(self, user_id):
        query = "SELECT username FROM users_login_details WHERE user_id = %s"
        data = self._execute_query(query, (user_id,), fetchone=True)
        return data["username"] if data else None
    
    # def add_user(self, user_data):
    #     query = """
    #         call crud_user(%s, %s, %s, %s, %s, %s) AS result
    #     """
    #     params = (
    #         user_data["org_id"],
    #         user_data["username"],
    #         user_data["password"],
    #         user_data["first_name"],
    #         user_data["created_by"],
    #         user_data["role_id"]
    #     )

    #     result = self._execute_query(query, params, fetchone=True)
    #     return result["result"]
    def register_user(self, login_user_id, name, password, orgid, clientid, role_id):
        try:
            params = (
                login_user_id,
                "CREATE",
                None,          # p_user_id (not needed for create)
                name,
                password,
                orgid,
                clientid,
                role_id
            )

            user=self._execute_procedure("crud_user", params)

            if user is None:
                return {
                    "status": "error",
                    "message": "Failed to create user"
                }

            return {
                "status": "success",
                "message": "User created successfully"
            }

        except Exception as e:
            print("Register user error:", e)
            return {
                "status": "error",
                "message": "Failed to create user"
            }
        
    def change_password(self, name, new_password):
        query = "UPDATE user SET password = %s WHERE name = %s"
        params = (new_password, name)
        self._execute_query(query, params)

    def crud_user(self, login_user_id, action,
                user_id=None,
                name=None,
                password=None,
                orgid=None,
                clientid=None,
                role_id=None):

        params = (
            login_user_id,
            action,
            user_id,
            name,
            password,
            orgid,
            clientid,
            role_id
        )

        result = self._execute_procedure("crud_user", params)

        return result


    def add_user_without_email(self, user_data):
        query = """
            INSERT INTO users_login_details (username, password_hash, created_by, created_on)
            VALUES (%s, %s, %s, NOW())
        """
        params = (user_data["username"], user_data["password"], "dev")
        self._execute_query(query, params)
        return user_data

    def delete_user(self, user_id):
        # Delete from both personal_details and login_details
        self._execute_query("DELETE FROM users_personal_details WHERE user_id = %s", (user_id,))
        self._execute_query("DELETE FROM users_login_details WHERE user_id = %s", (user_id,))

    # ------------------------- Site Table Operations -------------------------

    def add_site(self, site_data, user_id):
        query = """
            INSERT INTO sites_sites (name, location, status, created_by, created_on)
            VALUES (%s, %s, %s, %s, NOW())
        """
        params = (site_data["name"], site_data["location"], site_data["status"], user_id)
        self._execute_query(query, params)
        return site_data

    def get_sites_by_user(self, user_id):
        query = "SELECT * FROM sites_sites WHERE created_by = %s"
        return self._execute_query(query, (user_id,), fetchall=True)

    def delete_sites_by_site_id(self, site_id):
        try:
            self._execute_query("DELETE FROM sites_device WHERE site_id = %s", (site_id,))
            self._execute_query("DELETE FROM sites_sites WHERE site_id = %s", (site_id,))
            return True
        except Exception as e:
            print(f"Error deleting site: {e}")
            return False

    # ------------------------- Device Table Operations -------------------------

    def get_all_devices(self,user_id):
        proc_name = "get_devices_by_role"
        params = (user_id,)

        result = self._execute_procedure(proc_name, params)
        if not result:
            return []
        return result

    def add_device(self, design_info, sales_info, production_info,
               user_id, site_id, expiry_date):

        params = (
            # --- design_info ---
            design_info.get("version"),
            design_info.get("hardware"),
            design_info.get("database"),
            design_info.get("os"),
            design_info.get("url"),

            # --- sales_info ---
            sales_info.get("salesDate"),
            sales_info.get("customerName"),
            sales_info.get("orderNumber"),
            sales_info.get("quantityOrdered"),
            sales_info.get("invoiceNumber"),
            sales_info.get("deliveryDate"),
            sales_info.get("salesperson"),
            sales_info.get("price"),
            sales_info.get("remarks"),

            # --- production_info ---
            production_info.get("serialNumber"),
            production_info.get("productName"),
            production_info.get("status"),

            # --- device ---
            site_id,
            user_id,
            expiry_date
        )

        result = self._execute_procedure("add_device", params)

        # Stored procedure returns JSON_OBJECT as result
        if result and len(result) > 0:
            return result[0]["result"]

        return None


    def get_device(self, user_id,device_id):
        params = (user_id,device_id)
        rows = self._execute_procedure("get_device_json",params)
        if rows and len(rows) > 0:
      
        # Stored procedure column name = device_json
            return json.loads(rows[0]["device_json"])

        return None

    def update_device(self, device_id, design_info, sales_info,
                  production_info, expiry_date, site_id,user_id):

        params = (
            # --- core device ---
            user_id,
            device_id,
            site_id,
            expiry_date,

            # --- design ---
            design_info.get("version"),
            design_info.get("hardware"),
            design_info.get("database"),
            design_info.get("os"),
            design_info.get("url"),

            # --- sales ---
            sales_info.get("salesDate"),
            sales_info.get("customerName"),
            sales_info.get("orderNumber"),
            sales_info.get("quantityOrdered"),
            sales_info.get("invoiceNumber"),
            sales_info.get("deliveryDate"),
            sales_info.get("salesperson"),
            sales_info.get("price"),
            sales_info.get("remarks"),

            # --- production ---
              # --- production (FIXED KEYS) ---
            production_info.get("serialNumber"),
            production_info.get("productName"),
            production_info.get("status"),
        )

        result = self._execute_procedure("update_device_master", params)

        if result and len(result) > 0:
            return result[0]["result"]

        return {"status": "FAILED", "message": "No response from procedure"}


    def delete_device(self, user_id,device_id):
        params = (user_id, device_id)
        rows = self._execute_procedure("delete_device_by_role", params)

        if rows and len(rows) > 0:
            return json.loads(rows[0]["result"])

        return {
            "status": "ERROR",
            "message": "No response from procedure"
        }


    def add_device_by_user(self, device_name, device_url, site_id, user_id):
        query = """
            INSERT INTO sites_device (site_id, device_name, device_url, created_by, created_on)
            VALUES (%s, %s, %s, %s, NOW())
        """
        params = (site_id, device_name, device_url, user_id)
        self._execute_query(query, params)

        result = self._execute_query("SELECT LAST_INSERT_ID() as device_id", fetchone=True)
        return result["device_id"] if result else None

    def get_device_url_by_device_id(self, device_id):
        query = """
            SELECT di.url
            FROM device d
            JOIN design_info di ON d.design_id = di.id
            WHERE d.id = %s
        """

        row = self._execute_query(query, (device_id,), fetchone=True)

        url = row["url"] if row else None

        return url

    
    def get_all_organizations_from_db(self):
        # MySQL functions are called using SELECT
        query = "SELECT get_all_organizations() AS org_data"
        result = self._execute_query(query, fetchone=True)
        if result and result['org_data']:
            # MySQL returns the JSON as a string, so we parse it
            return json.loads(result['org_data'])
        return []
    
    def add_organization_db(self, org_data, created_by):
        # The SQL query to call your MySQL function
        query = "SELECT add_organization(%s, %s, %s, %s, %s) AS response"
        
        params = (
            org_data.get('name'),
            org_data.get('address'),
            org_data.get('website_url'),
            org_data.get('logo_url'),
            created_by
        )

        # Use fetchone=True to get the JSON result
        result = self._execute_query(query, params, fetchone=True)

        if result and result['response']:
            # MySQL returns the JSON as a string; parse it to Python dict
            return json.loads(result['response'])
        
        return {"status": "false", "message": "Failed to add organization", "data": None}
    
    def get_all_users(self):
        query = "SELECT get_all_user() AS result"
        data = self._execute_query(query, fetchone=True)
        
        if data and data['result']:
                # MySQL returns the JSON as a string, so we parse it
                return json.loads(data['result'])
        return []

    

    def get_all_roles(self):
        query = "SELECT * FROM role "
        data = self._execute_query(query, fetchall=True)

        if data :
                # MySQL returns the JSON as a string, so we parse it
                return data
        return []

    def add_site_org(self, site_data: dict, user_id: int):
        query = """
            SELECT add_site(%s, %s, %s, %s) AS result
        """

        params = (
            site_data["name"],
            site_data["location"],
            site_data["org_id"],
            user_id
        )

        result = self._execute_query(query, params, fetchone=True)

        return result["result"]
    
    def get_all_devices_by_user(self,id):
        query = "SELECT * FROM sites_device WHERE created_by = %s"
        return self._execute_query(query, (id,), fetchall=True)
    
        
    def delete_device_by_user(self, device_id, user_id,site_id,created_by):
        query = "DELETE FROM sites_device WHERE device_id = %s AND created_by = %s"
        self._execute_query(query, (device_id, user_id))

    def device_registration(self, design, sales, production, user_id, site_id):
        with self._with_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("""
                    INSERT INTO design_info (version, hardware, database, os)
                    VALUES (%s, %s, %s, %s)
                """, (design['version'], design['hardware'],
                      design['database'], design['os']))
                design_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO sales_info
                    (sales_date, customer_name, order_number, quantity_ordered,
                    invoice_number, delivery_date, salesperson, price, remarks)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    sales['salesDate'], sales['customerName'],
                    sales['orderNumber'], sales['quantityOrdered'],
                    sales['invoiceNumber'], sales['deliveryDate'],
                    sales['salesperson'], sales['price'], sales['remarks']
                ))
                sales_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO production_info
                    (serial_number, product_name, status)
                    VALUES (%s,%s,%s)
                """, (
                    production['serialNumber'],
                    production['productName'],
                    production['status']
                ))
                production_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO sites_device
                    (site_id, last_seen, design_id, sales_id, production_id,
                    created_on, created_by)
                    VALUES (%s, NOW(), %s, %s, %s, NOW(), %s)
                """, (site_id, design_id, sales_id, production_id, user_id))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise
            finally:
                cursor.close()


    def get_organization(self, user_id: int, action: str, org_id=None, org_name=None):

        params = (user_id, action, org_id, org_name)

        try:
            result = self._execute_procedure("crud_organization", params)

            # READ returns rows
            if action == "READ":
                return result if result else []

            # CREATE / UPDATE / DELETE success message
            return {"message": f"{action} operation completed successfully"}

        except Exception as e:
            print("DB Error:", e)
            return None
        

    # def get_organization(self, user_id: int, action: str, org_id=None, org_name=None):
    #         query = "CALL crud_client(%s, %s, %s, %s)"

    #         params = (user_id, action, org_id, org_name)

    #         try:
    #             result = self._execute_query(query, params, fetchall=True)

    #             # READ returns rows
    #             if action == "READ":
    #                 return result if result else []

    #             # CREATE / UPDATE / DELETE success message
    #             return {"message": f"{action} operation completed successfully"}

    #         except Exception as e:
    #             print("DB Error:", e)
    #             return None
            
    def crud_client(self, user_id: int, action: str, client_id=None, client_name=None, org_id=None):
        params = (user_id, action, client_id, client_name, org_id)
        try:
            result = self._execute_procedure("crud_client", params)

            return {
                "success": True,
                "message": f"{action} executed successfully",
                "data": result or []
            }

        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "data": []
            }
    def crud_site(self, user_id, action, site_id=None, site_name=None, client_id=None):
        params = (user_id, action, site_id, site_name, client_id)
        try:
            result = self._execute_procedure("crud_site", params)
            return {
                "success": True,
                "message": f"{action} executed successfully",
                "sites": result or []
            }

        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "sites": []
            }


db = DatabaseAccess()

# if __name__ == "__main__":
#     db = DatabaseAccess()
#     # Example usage
#     print(db.get_all_devices(102))