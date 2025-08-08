import requests
import json
import time

# A dynamic catalog of server types with their characteristics.
SERVER_CATALOG = [
    {
        "name": "SQL Server",
        "workload_type": "database",
        "description": "Primary database server for OLTP workloads.",
        "categories": {
            "general-purpose": {
                "small_payer_threshold": "Standard_D2s_v5",
                "large_payer_threshold": "Standard_D16s_v5"
            },
            "memory-optimized": {
                "small_payer_threshold": "Standard_E2s_v5",
                "large_payer_threshold": "Standard_E16s_v5"
            },
            "compute-optimized": {
                "small_payer_threshold": "Standard_F2s_v2",
                "large_payer_threshold": "Standard_F16s_v2"
            }
        }
    },
    {
        "name": "Batch/App Server",
        "workload_type": "application",
        "description": "Server for batch and application workloads.",
        "categories": {
            "general-purpose": {
                "small_payer_threshold": "Standard_D2as_v4",
                "large_payer_threshold": "Standard_D16as_v4"
            },
            "memory-optimized": {
                "small_payer_threshold": "Standard_E2as_v5",
                "large_payer_threshold": "Standard_E16as_v5"
            },
            "compute-optimized": {
                "small_payer_threshold": "Standard_F2s_v2",
                "large_payer_threshold": "Standard_F16s_v2"
            }
        }
    },
    {
        "name": "API/FXI Server",
        "workload_type": "application",
        "description": "Server for API/FXI workloads.",
        "categories": {
            "general-purpose": {
                "small_payer_threshold": "Standard_D2as_v4",
                "large_payer_threshold": "Standard_D16as_v4"
            },
            "memory-optimized": {
                "small_payer_threshold": "Standard_E2as_v5",
                "large_payer_threshold": "Standard_E16as_v5"
            },
            "compute-optimized": {
                "small_payer_threshold": "Standard_F2s_v2",
                "large_payer_threshold": "Standard_F16s_v2"
            }
        }
    },
    {
        "name": "HIPAA Gateway Server",
        "workload_type": "application",
        "description": "Server for HIPAA Gateway workloads.",
        "categories": {
            "general-purpose": {
                "small_payer_threshold": "Standard_D2as_v4",
                "large_payer_threshold": "Standard_D16as_v4"
            },
            "memory-optimized": {
                "small_payer_threshold": "Standard_E2as_v5",
                "large_payer_threshold": "Standard_E16as_v5"
            },
            "compute-optimized": {
                "small_payer_threshold": "Standard_F2s_v2",
                "large_payer_threshold": "Standard_F16s_v2"
            }
        }
    },
    {
        "name": "WorkFlow Server",
        "workload_type": "application",
        "description": "Server for WorkFlow workloads.",
        "categories": {
            "general-purpose": {
                "small_payer_threshold": "Standard_D2as_v4",
                "large_payer_threshold": "Standard_D16as_v4"
            },
            "memory-optimized": {
                "small_payer_threshold": "Standard_E2as_v5",
                "large_payer_threshold": "Standard_E16as_v5"
            },
            "compute-optimized": {
                "small_payer_threshold": "Standard_F2s_v2",
                "large_payer_threshold": "Standard_F16s_v2"
            }
        }
    },
    {
        "name": "NetworX Server",
        "workload_type": "application",
        "description": "Server for NetworX workloads.",
        "categories": {
            "general-purpose": {
                "small_payer_threshold": "Standard_D2as_v4",
                "large_payer_threshold": "Standard_D16as_v4"
            },
            "memory-optimized": {
                "small_payer_threshold": "Standard_E2as_v5",
                "large_payer_threshold": "Standard_E16as_v5"
            },
            "compute-optimized": {
                "small_payer_threshold": "Standard_F2s_v2",
                "large_payer_threshold": "Standard_F16s_v2"
            }
        }
    },
    {
        "name": "Surround Server",
        "workload_type": "application",
        "description": "Server for Surround workloads.",
        "categories": {
            "general-purpose": {
                "small_payer_threshold": "Standard_D2as_v4",
                "large_payer_threshold": "Standard_D16as_v4"
            },
            "memory-optimized": {
                "small_payer_threshold": "Standard_E2as_v5",
                "large_payer_threshold": "Standard_E16as_v5"
            },
            "compute-optimized": {
                "small_payer_threshold": "Standard_F2s_v2",
                "large_payer_threshold": "Standard_F16s_v2"
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


def get_azure_recommendations(subscriber_count, server_configs):
    """
    Generates a list of recommended Azure resources dynamically from the catalog
    based on the category selected for each server.
    """
    recommendations = {}
    
    # A mapping from the server name in the catalog to its details
    server_catalog_map = {server["name"]: server for server in SERVER_CATALOG}

    # Iterate through the server configurations from the frontend
    for server_name, config in server_configs.items():
        server_type_info = server_catalog_map.get(server_name)
        if not server_type_info:
            continue

        category = config.get("category")
        if not category:
            continue

        vm_series = ""
        category_tiers = server_type_info["categories"].get(category)
        
        if category_tiers:
            if subscriber_count < 1000000:
                vm_series = category_tiers["small_payer_threshold"]
            else:
                vm_series = category_tiers["large_payer_threshold"]
            
        recommendations[server_name] = {
            "vm_series": vm_series,
            "workload_type": server_type_info["workload_type"],
        }
    
    # Note: Storage recommendation is now de-coupled from server recommendations
    # as it's not tied to a specific server's category.
    # We can add a separate UI for storage options later if needed.

    return recommendations

def fetch_all_vm_prices(region="eastus", operating_system="windows"):
    """
    Fetches all VM prices for a given region in a single, paginated API call.
    Returns a dictionary mapping SKU names to their hourly prices.
    """
    api_url = "https://prices.azure.com/api/retail/prices"
    
    os_filter = ""
    if operating_system == "windows":
        os_filter = " and contains(productName, 'Windows')"
    # For Linux, we don't add an OS filter, as the base price is typically the Linux price.

    filter_string = (
        f"serviceName eq 'Virtual Machines' and "
        f"armRegionName eq '{region}' and "
        f"priceType eq 'Consumption' and "
        f"unitOfMeasure eq '1 Hour'{os_filter}"
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

def get_total_estimated_monthly_cost(environment_name, subscriber_count, price_tolerance, region="eastus", operating_system="windows", hours_in_month=730, server_configs={}):
    """
    Calculates the total estimated monthly cost for an environment using a pre-fetched price list and dynamic server counts.
    """
    vm_prices = fetch_all_vm_prices(region=region, operating_system=operating_system)
    storage_prices = fetch_all_storage_prices(region)
    
    if not vm_prices or not storage_prices:
        print("\nFailed to fetch pricing data. Cannot calculate costs.")
        return {}, 0.0

    recommendations = get_azure_recommendations(subscriber_count, server_configs)
    total_cost = 0.0
    
    print(f"\n--- Pricing Estimate for {environment_name}: {subscriber_count} Subscribers ({price_tolerance.upper()}) ---")

    itemized_costs = {}
    
    for server_name, config in recommendations.items():
        server_config_from_user = server_configs.get(server_name, {})
        server_count = server_config_from_user.get("count", 0)

        if server_count == 0:
            continue

        if config["workload_type"] == "database" or config["workload_type"] == "application":
            vm_sku = config["vm_series"]
            hourly_price = vm_prices.get(vm_sku)
            
            if hourly_price is not None:
                monthly_cost = hourly_price * hours_in_month * server_count
                total_cost += monthly_cost
                print(f"- {server_name} ({vm_sku}) x {server_count}: ${monthly_cost:.2f} per month")
                itemized_costs[server_name] = {
                    "sku": vm_sku,
                    "count": server_count,
                    "category": server_config_from_user.get("category", "N/A"),
                    "monthly_cost": monthly_cost
                }
            else:
                print(f"- Could not find price for {server_name} ({vm_sku}).")

    # Handle storage separately
    storage_tier = STORAGE_CATALOG[0]['tiers'][price_tolerance]
    storage_name = STORAGE_CATALOG[0]['name']
    storage_size_gb = 1024  # Example: 1 TB

    if storage_tier == "Standard_SSD_LRS_Disk_Size_P10":
        api_sku = "Standard SSD LRS Disk Size P10"
    elif storage_tier == "Premium_SSD_LRS_Disk_Size_P20":
        api_sku = "Premium SSD LRS Disk Size P20"
    elif storage_tier == "Premium_SSD_LRS_Disk_Size_P30":
        api_sku = "Premium SSD LRS Disk Size P30"
    else:
        api_sku = storage_tier

    monthly_price_per_gb = storage_prices.get(api_sku)
    if monthly_price_per_gb is not None:
        monthly_cost = monthly_price_per_gb * storage_size_gb
        total_cost += monthly_cost
        print(f"- {storage_name} ({storage_tier}): ${monthly_cost:.2f} per month")
        itemized_costs[storage_name] = {
            "sku": storage_tier,
            "count": storage_size_gb,
            "monthly_cost": monthly_cost,
            "category": price_tolerance
        }
    else:
        print(f"- Could not find price for {storage_tier}.")

    print(f"\nTOTAL ESTIMATED MONTHLY COST: ${total_cost:.2f}")
    
    return itemized_costs, total_cost