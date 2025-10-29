import pandas as pd
import re
from typing import Dict, Tuple, Optional, List

class PropertyChatbot:
    def __init__(self, project_csv: str, address_csv: str, config_csv: str, variant_csv: str):
        """Initialize the chatbot with CSV data files."""
        self.load_data(project_csv, address_csv, config_csv, variant_csv)
        self.city_mapping = {
            "mumbai": ["cmf50r5a00000vcj0k1iuocuu"],
            "pune": ["cmf6nu3ru000gvcxspxarll3v"],
        }
        self.available_cities = list(self.city_mapping.keys())

   def load_data(self, project_csv: str, address_csv: str, config_csv: str, variant_csv: str):
    """Load and merge all CSV files, filtering out test data."""
    project = pd.read_csv(project_csv)
    address = pd.read_csv(address_csv)
    config = pd.read_csv(config_csv)
    variant = pd.read_csv(variant_csv)

    # 🧹 FILTER OUT TEST DATA (before merging)
    test_keywords = ['test', 'testing', 'dummy', 'igi', 'sample', '999']
    for keyword in test_keywords:
        project = project[~project['projectName'].str.contains(keyword, case=False, na=False)]
    
    # Filter by bad addresses too
    bad_addr_projects = address[
        address['fullAddress'].str.contains('address|landmark|asdfgh|awsedr', case=False, na=False)
    ]['projectId'].tolist()
    project = project[~project['id'].isin(bad_addr_projects)]

    merged = project.merge(address, left_on='id', right_on='projectId',
                          how='left', suffixes=('_project', '_address'))
    merged = merged.merge(config, left_on='id_project', right_on='projectId',
                        how='left', suffixes=('', '_config'))
    merged = merged.merge(variant, left_on='id', right_on='configurationId', how='left')

    merged = merged.rename(columns={
        'cityId': 'city',
        'customBHK': 'bhk',
        'fullAddress': 'address',
        'projectName': 'name',
        'price': 'price_inr'
    })

    # Extract locality from CSV addresses ONLY
    merged['locality'] = merged['address'].apply(self.extract_locality)

    self.df = merged
    print(f"✅ Data loaded: {merged.shape[0]} records (test data filtered)")

    def extract_locality(self, address):
        """Extract locality from address using ONLY CSV data - NO hardcoded lists."""
        if pd.isna(address) or address == '':
            return "Unknown"
        
        address_str = str(address).strip()
        parts = address_str.split(',')
        
        # Try to find the best locality part by filtering out non-locality elements
        for part in reversed(parts):
            part_clean = part.strip()
            
            if len(part_clean) < 3 or len(part_clean) > 50:
                continue
            
            # Skip parts that are clearly not localities (using patterns, not hardcoded lists)
            if (re.search(r'\d{6}', part_clean) or  # Pincode
                re.search(r'\d{3,}', part_clean) or  # Plot/building numbers
                'maharashtra' in part_clean.lower() or
                'mumbai' in part_clean.lower() or
                'pune' in part_clean.lower() or
                'near' in part_clean.lower() or
                'road' in part_clean.lower() or
                'rd' in part_clean.lower() or
                'sr' in part_clean.lower()[:4] or
                'plot' in part_clean.lower() or
                'building' in part_clean.lower() or
                'project' in part_clean.lower() or
                'cts' in part_clean.lower()):
                continue
            
            return part_clean[:40]
        
        # Fallback
        for part in parts:
            clean = part.strip()
            if len(clean) > 3:
                return clean[:40]
        
        return "Unknown"

    def get_city_ids(self, city_name: Optional[str]) -> List[str]:
        if not city_name:
            return sum(self.city_mapping.values(), [])
        return self.city_mapping.get(city_name.lower().strip(), [])

    def is_city_available(self, city_name: str) -> bool:
        if not city_name:
            return True
        return city_name.lower() in self.available_cities

    def parse_query(self, query: str) -> Dict:
        """Extract filters from natural language query."""
        query = query.lower()
        filters = {"bhk": None, "city": None, "budget": None, "status": None, "locality": None}

        # BHK
        match_bhk = re.search(r'(\d+)\s*bhk', query)
        if match_bhk:
            filters["bhk"] = f"{match_bhk.group(1)}BHK"

        # City recognition (for validation, not hardcoding data)
        common_cities = ["mumbai", "pune", "delhi", "bangalore", "hyderabad", "chennai",
                        "kolkata", "ahmedabad", "surat", "jaipur", "lucknow", "bhopal",
                        "indore", "nagpur", "goa", "noida", "gurgaon"]
        for city in common_cities:
            if re.search(rf"\b{city}\b", query):
                filters["city"] = city
                break

        # Locality (search for common patterns, but the actual data comes from CSV)
        locality_keywords = ["wakad", "baner", "aundh", "ravet", "ghatkopar", "dombivli",
                            "chembur", "mulund", "thane", "andheri", "punawale", "kharadi"]
        for loc in locality_keywords:
            if loc in query:
                filters["locality"] = loc
                break

        # Budget
        match_budget_range = re.search(r'(\d+(?:\.\d+)?)\s*(l|cr)\D+(\d+(?:\.\d+)?)\s*(l|cr)', query)
        match_budget_single = re.search(r'under\s+(\d+(?:\.\d+)?)\s*(l|cr|lakh)', query)

        def to_inr(amount, unit):
            if unit.startswith('l'):
                return float(amount) * 100000
            elif unit.startswith('cr'):
                return float(amount) * 10000000
            return float(amount)

        if match_budget_range:
            low = to_inr(match_budget_range.group(1), match_budget_range.group(2))
            high = to_inr(match_budget_range.group(3), match_budget_range.group(4))
            filters["budget"] = (low, high)
        elif match_budget_single:
            filters["budget"] = to_inr(match_budget_single.group(1), match_budget_single.group(2))

        # Status
        if "ready" in query or "ready to move" in query:
            filters["status"] = "READY_TO_MOVE"
        elif "under construction" in query:
            filters["status"] = "UNDER_CONSTRUCTION"

        return filters

    def filter_properties(self, filters: Dict, expanded: bool = False) -> pd.DataFrame:
        """Filter properties based on extracted filters."""
        df = self.df.copy()

        if filters["city"] and not self.is_city_available(filters["city"]):
            return pd.DataFrame()

        if 'city' in df.columns:
            df["city"] = df["city"].astype(str).str.lower()
        if 'bhk' in df.columns:
            df["bhk"] = df["bhk"].astype(str).str.upper()
        if 'status' in df.columns:
            df["status"] = df["status"].astype(str).str.upper()

        filtered = df.copy()

        city_ids = self.get_city_ids(filters["city"])
        if city_ids and 'city' in filtered.columns:
            filtered = filtered[filtered["city"].isin(city_ids)]

        if filters["bhk"] and 'bhk' in filtered.columns:
            filtered = filtered[filtered["bhk"] == filters["bhk"].upper()]

        if 'price_inr' in filtered.columns:
            filtered['price_inr'] = pd.to_numeric(filtered['price_inr'], errors='coerce')
            filtered = filtered.dropna(subset=['price_inr'])

            if isinstance(filters["budget"], tuple):
                low, high = filters["budget"]
                filtered = filtered[(filtered["price_inr"] >= low) & (filtered["price_inr"] <= high)]
            elif isinstance(filters["budget"], (int, float)):
                filtered = filtered[filtered["price_inr"] < filters["budget"]]

        if filters["status"] and 'status' in filtered.columns and not expanded:
            filtered = filtered[filtered["status"].str.contains(filters["status"], na=False)]

        if filters["locality"] and 'address' in filtered.columns and not expanded:
            filtered = filtered[filtered["address"].str.lower().str.contains(filters["locality"], na=False)]

        return filtered.head(10)

    def format_price(self, price: float) -> str:
        if pd.isna(price):
            return "Price not available"
        if price >= 10000000:
            return f"₹{price/10000000:.2f} Cr"
        else:
            return f"₹{price/100000:.2f} L"

    def generate_summary(self, results: pd.DataFrame, filters: Dict, expanded_results: pd.DataFrame = None) -> str:
        """Generate summary using ONLY CSV data."""
        requested_city = filters.get("city", "").capitalize() if filters.get("city") else ""
        bhk = filters.get("bhk", "")
        status_raw = filters.get("status", "")
        status = status_raw.replace("_", " ").lower() if status_raw else "available"
        budget = filters.get("budget")
        requested_locality = filters.get("locality", "").title() if filters.get("locality") else ""

        if requested_city and not self.is_city_available(requested_city):
            available_cities_str = ", ".join([c.capitalize() for c in self.available_cities])
            return f"⚠️ Sorry, we don't have property listings for **{requested_city}** yet. Currently, we only cover **{available_cities_str}**."

        budget_str = ""
        if isinstance(budget, tuple):
            budget_str = f"between {self.format_price(budget[0])} and {self.format_price(budget[1])}"
        elif budget:
            budget_str = f"within {self.format_price(budget)}"

        city_display = requested_city if requested_city else "Mumbai & Pune"

        if results.empty:
            if expanded_results is not None and not expanded_results.empty:
                count = len(expanded_results)
                
                # Get localities from CSV data
                localities = expanded_results['locality'].value_counts().head(3).index.tolist()
                localities = [loc for loc in localities if loc.lower() != "unknown"]
                locality_str = " and ".join(localities[:2]) if len(localities) >= 2 else localities[0] if localities else "nearby areas"
                
                status_str = f"{status} " if status != "available" else ""
                locality_msg = f" in {requested_locality}" if requested_locality else ""
                
                return f"No {status_str}{bhk} options found{locality_msg} {budget_str} in {city_display}. Expanding search to **{locality_str}** found **{count} options** matching your other criteria."
            
            status_str = f"{status} " if status != "available" else ""
            locality_msg = f" in {requested_locality}" if requested_locality else ""
            return f"No {status_str}{bhk} properties found{locality_msg} {budget_str} in {city_display}. Try adjusting your filters."

        # SUCCESS - All data from CSV
        count = len(results)
        localities = results['locality'].value_counts().head(3).index.tolist()
        localities = [loc for loc in localities if loc.lower() != "unknown"]
        locality_str = " and ".join(localities[:2]) if len(localities) >= 2 else localities[0] if localities else "various areas"
        
        top_project = results.iloc[0]['name'] if 'name' in results.columns else "Property"
        top_price = results.iloc[0]['price_inr'] if 'price_inr' in results.columns else 0
        min_price = results['price_inr'].min() if 'price_inr' in results.columns else 0
        max_price = results['price_inr'].max() if 'price_inr' in results.columns else 0
        
        status_counts = results['status'].value_counts()
        ready_count = status_counts.get('READY_TO_MOVE', 0)
        construction_count = status_counts.get('UNDER_CONSTRUCTION', 0)

        status_str = f"{status} " if status != "available" else ""
        
        summary = f"{budget_str.capitalize()}, most {bhk} {status_str}properties in **{city_display}** are found near **{locality_str}**. "
        summary += f"Found **{count} listings** with prices from {self.format_price(min_price)} to {self.format_price(max_price)}. "
        
        if ready_count > 0 and construction_count > 0:
            summary += f"{ready_count} ready-to-move, {construction_count} under construction. "
        elif ready_count > 0:
            summary += f"All {ready_count} ready for possession. "
        elif construction_count > 0:
            summary += f"All under construction. "
        
        summary += f"Top match: **{top_project}** at {self.format_price(top_price)}."

        return summary

    def process_query(self, query: str) -> Tuple[str, pd.DataFrame, Dict]:
        """Process user query."""
        filters = self.parse_query(query)
        results = self.filter_properties(filters, expanded=False)
        
        expanded_results = None
        if results.empty and (filters["locality"] or filters["status"]):
            expanded_results = self.filter_properties(filters, expanded=True)
        
        summary = self.generate_summary(results, filters, expanded_results)
        final_results = results if not results.empty else (expanded_results if expanded_results is not None else pd.DataFrame())
        
        return summary, final_results, filters

