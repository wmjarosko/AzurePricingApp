import requests
import json
import time

# A dynamic catalog of server types with their characteristics.
# The `server_count` field has been removed as it will now be provided by the front-end.
SERVER_CATALOG = [
    {
        "name": "SQL Server",
        "workload_type": "database",
        "description": "Primary database server for OLTP workloads.",
        "tiers": {
            "cost-optimized": {
                # Updated from Standard_DS2_v2 to a newer, supported SKU
                "small_payer_threshold": "Standard_D2as_v5", 
                "large_payer_threshold": "Standard_DS4_v2"   
            },
            "balanced": {
                "small_payer_threshold": "Standard_D4s_v3",
                "large_payer_threshold": "Standard_D8s_v3"
            },
            "performance-first": {
                "small_payer_threshold": "Standard_E8s_v3",
                "large_payer_threshold": "Standard_E16s_v3"
            }
        }
    },
    {
        "name": "Batch Processor",
        "workload_type": "application",
        "description": "Windows server for nightly batch jobs.",
        "tiers": {
            "cost-optimized": {
                "small_payer_threshold": "Standard_B2s",
                "large_payer_threshold": "Standard_B4ms"
            },
            "balanced": {
                "small_payer_threshold": "Standard_D2s_v3",
                "large_payer_threshold": "Standard_D4s_v3"
            },
            "performance-first": {
                "small_payer_threshold": "Standard_F4s_v2",
                "large_payer_threshold": "Standard_F8s_v2"
            }
        }
    },
]

# A new catalog for storage, which we'll use for databases
STORAGE_CATALOG = [
    {
        "name": "Database Storage",
        "workload_type": "storage",
        "description": "Premium storage for database workloads.",
        "tiers": {
            "cost-optimized": "Standard_SSD_LRS_Disk_Size_P10",
            "balanced": "Premium_SSD_LRS_Disk_Size_P20",
            "performance-first": "Premium_SSD_LRS_Disk_Size_P30",
        }
    }
]


def get_azure_recommendations(subscriber_count, price_tolerance):
    """
    Generates a list of recommended Azure resources dynamically from the catalog.
    """
    recommendations = {}
    
    # Iterate through our dynamic catalog to build the recommendations
    for server_type in SERVER_CATALOG:
        vm_series = ""
        tier = server_type["tiers"][price_tolerance]
        
        if subscriber_count < 1000000:
            vm_series = tier["small_payer_threshold"]
        else:
            vm_series = tier["large_payer_threshold"]
            
        recommendations[server_type["name"]] = {
            "vm_series": vm_series,
            "workload_type": server_type["workload_type"],
        }
    
    
    # Also add the storage recommendation
    for storage_type in STORAGE_CATALOG:
        storage_sku = storage_type["tiers"][price_tolerance]
        recommendations[storage_type["name"]] = {
            "storage_sku": storage_sku,
            "workload_type": storage_type["workload_type"],
            "name": storage_type["name"]
        }

    return recommendations

def fetch_all_vm_prices(region="eastus"):
    """
    Fetches all VM prices for a given region in a single, paginated API call.
    Returns a dictionary mapping SKU names to their hourly prices.
    """
    api_url = "https://prices.azure.com/api/retail/prices"
    
    filter_string = (
        f"serviceName eq 'Virtual Machines' and "
        f"armRegionName eq '{region}' and "
        f"priceType eq 'Consumption' and "
        f"unitOfMeasure eq '1 Hour'"
    )
    
    all_prices = {}
    next_page_link = api_url
    params = {"$filter": filter_string}
    
    retries = 3
    for i in range(retries):
        try:
            if i > 0 and next_page_link:
                response = requests.get(next_page_link)
            else:
                response = requests.get(api_url, params=params)

            response.raise_for_status()
            
            data = response.json()
            
            for item in data.get("Items", []):
                sku = item.get("armSkuName")
                price = item.get("retailPrice")
                if sku and price:
                    all_prices[sku] = price
            
            next_page_link = data.get("NextPageLink")
            if not next_page_link:
                break

            time.sleep(1) # Add a small delay between paginated requests

        except requests.exceptions.RequestException as e:
            if i < retries - 1:
                time.sleep(2**(i+1))
            else:
                print(f"Final attempt to fetch prices failed: {e}")
                break

    return all_prices

def fetch_all_storage_prices(region="eastus"):
    """
    Fetches all storage prices for a given region.
    Returns a dictionary mapping SKU names to their hourly prices.
    """
    api_url = "https://prices.azure.com/api/retail/prices"
    
    filter_string = (
        f"serviceName eq 'Storage' and "
        f"armRegionName eq '{region}' and "
        f"priceType eq 'Consumption' and "
        f"unitOfMeasure eq '1 GB/Month'"
    )

    params = {"$filter": filter_string}
    all_prices = {}
    
    retries = 3
    for i in range(retries):
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            for item in data.get("Items", []):
                sku = item.get("skuName") # Storage uses skuName, not armSkuName
                price = item.get("retailPrice")
                if sku and price:
                    all_prices[sku] = price
            
            # Storage pricing is not paginated, so we don't need a loop for NextPageLink
            break

        except requests.exceptions.RequestException as e:
            if i < retries - 1:
                time.sleep(2**(i+1))
            else:
                print(f"Final attempt to fetch storage prices failed: {e}")
                break

    return all_prices

# This function has been updated to accept the `server_counts` dictionary
def get_total_estimated_monthly_cost(subscriber_count, price_tolerance, region="eastus", hours_in_month=730, server_counts={}):
    """
    Calculates the total estimated monthly cost for an environment using a pre-fetched price list and dynamic server counts.
    """
    # Fetch all VM and storage prices once before calculating
    vm_prices = fetch_all_vm_prices(region)
    storage_prices = fetch_all_storage_prices(region)
    
    if not vm_prices or not storage_prices:
        print("\nFailed to fetch pricing data. Cannot calculate costs.")
        return {}, 0.0

    recommendations = get_azure_recommendations(subscriber_count, price_tolerance)
    total_cost = 0.0
    
    print(f"\n--- Pricing Estimate for {subscriber_count} Subscribers ({price_tolerance.upper()}) ---")

    itemized_costs = {}
    
    for server_name, config in recommendations.items():
        if config["workload_type"] == "database" or config["workload_type"] == "application":
            vm_sku = config["vm_series"]
            # Use the count from the server_counts dictionary, or default to 1
            server_count = server_counts.get(server_name, 1)
            
            hourly_price = vm_prices.get(vm_sku)
            
            if hourly_price is not None:
                monthly_cost = hourly_price * hours_in_month * server_count
                total_cost += monthly_cost
                print(f"- {server_name} ({vm_sku}) x {server_count}: ${monthly_cost:.2f} per month")
                itemized_costs[server_name] = {
                    "sku": vm_sku,
                    "count": server_count,
                    "monthly_cost": monthly_cost
                }
            else:
                print(f"- Could not find price for {server_name} ({vm_sku}).")
        
        elif config["workload_type"] == "storage":
            storage_sku = config["storage_sku"]
            storage_name = config["name"]
            # We'll assume a default storage size, this can be made dynamic later
            storage_size_gb = 1024 # Example: 1 TB
            
            # The pricing API's `skuName` for Managed Disks has a different format, so we need to adjust the key to retrieve the price
            if storage_sku == "Standard_SSD_LRS_Disk_Size_P10":
                api_sku = "Standard SSD LRS Disk Size P10"
            elif storage_sku == "Premium_SSD_LRS_Disk_Size_P20":
                api_sku = "Premium SSD LRS Disk Size P20"
            elif storage_sku == "Premium_SSD_LRS_Disk_Size_P30":
                api_sku = "Premium SSD LRS Disk Size P30"
            else:
                api_sku = storage_sku

            monthly_price_per_gb = storage_prices.get(api_sku)
            
            if monthly_price_per_gb is not None:
                # Storage price is per GB, so we multiply by the size
                monthly_cost = monthly_price_per_gb * storage_size_gb
                total_cost += monthly_cost
                print(f"- {storage_name} ({storage_sku}): ${monthly_cost:.2f} per month")
                itemized_costs[storage_name] = {
                    "sku": storage_sku,
                    "count": storage_size_gb,
                    "monthly_cost": monthly_cost
                }
            else:
                print(f"- Could not find price for {storage_sku}.")

    print(f"\nTOTAL ESTIMATED MONTHLY COST: ${total_cost:.2f}")
    
    return itemized_costs, total_cost