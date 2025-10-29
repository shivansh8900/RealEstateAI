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
        print("🧹 Filtering test data...")
        
        # Remove test projects by name
        test_keywords = ['test', 'testing', 'dummy', 'igi', 'sample', '999', 'testring']
        for keyword in test_keywords:
            before = len(project)
            project = project[~project['projectName'].str.contains(keyword, case=False, na=False)]
            removed = before - len(project)
            if removed > 0:
                print(f"   Removed {removed} projects with '{keyword}' in name")
        
        # Remove projects with fake addresses
        print("🧹 Filtering fake addresses...")
        bad_patterns = ['address', 'landmark', 'asdfgh', 'awsedr', 'sdfgh', 'esrdfgh']
        bad_project_ids = []
        
        for pattern in bad_patterns:
            bad_addrs = address[
                address['fullAddress'].str.contains(pattern, case=False, na=False)
            ]['projectId'].tolist()
            bad_project_ids.extend(bad_addrs)
        
        bad_project_ids = list(set(bad_project_ids))  # Remove duplicates
        if bad_project_ids:
            before = len(project)
            project = project[~project['id'].isin(bad_project_ids)]
            removed = before - len(project)
            print(f"   Removed {removed} projects with fake addresses")

        # Merge datasets
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

        # Clean price data
        merged['price_inr'] = pd.to_numeric(merged['price_inr'], errors='coerce')
        merged = merged[merged['price_inr'] <= 1000000000]  # Remove outliers
        merged = merged.dropna(subset=['price_inr'])  # Remove missing prices

        # Clean BHK data
        merged['bhk'] = merged['bhk'].fillna('').astype(str).str.strip().str.upper()
        merged['bhk'] = merged['bhk'].replace('', 'NOT_SPECIFIED')

        # Extract locality from CSV addresses
        merged['locality'] = merged['address'].apply(self.extract_locality)

        self.df = merged
        print(f"✅ Data loaded: {merged.shape[0]} records (test data filtered)")
        print(f"💰 Price range: {self.format_price(merged['price_inr'].min())} - {self.format_price(merged['price_inr'].max())}")

    def extract_locality(self, address):
        """Extract locality from address using ONLY CSV data."""
        if pd.isna(address) or address == '':
            return "Unknown"
        
        address_str = str(address).strip()
        parts = address_str.split(',')
        
        # Try to find the best locality part
        for part in reversed(parts):
            part_clean = part.strip()
            
            if len(part_clean) < 3 or len(part_clean) > 50:
                continue
            
            # Skip parts that are clearly not localities
            skip_patterns = [
                r'\d{6}',  # Pincode
                r'\d{3,}',  # Plot/building numbers
                'maharashtra',
                'mumbai',
                'pune',
                'near',
                'road',
                r'\brd\b',
                r'^sr\s',
                'plot',
                'building',
                'project',
                'cts',
                'opposite',
                'beside',
                'no\.',
            ]
            
            skip = False
            for pattern in skip_patterns:
                if re.search(pattern, part_clean.lower()):
                    skip = True
                    break
            
            if not skip:
                return part_clean[:40]
        
        # Fallback to first meaningful part
        for part in parts:
            clean = part.strip()
            if len(clean) > 3 and not re.search(r'\d{6}', clean):
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
        query_lower = query.lower()
        filters = {
            "bhk": None,
            "city": None,
            "budget": None,
            "status": None,
            "locality": None,
            "project_name": None
        }

        # Project name
        project_names = self.df['name'].dropna().unique()
        for project in project_names:
            if str(project).lower() in query_lower:
                filters["project_name"] = str(project)
                break

        # BHK
        bhk_patterns = [r'(\d+)\s*bhk', r'(\d+)\s*bed', r'(\d+)\s*bedroom', r'(\d+)bhk']
        for pattern in bhk_patterns:
            match = re.search(pattern, query_lower)
            if match:
                filters["bhk"] = f"{match.group(1)}BHK"
                break

        # City
        common_cities = ["mumbai", "pune", "delhi", "bangalore", "bengaluru", "hyderabad",
                        "chennai", "kolkata", "ahmedabad", "bhopal", "indore", "nagpur"]
        for city in common_cities:
            if re.search(rf"\b{city}\b", query_lower):
                filters["city"] = city
                break

        # Locality
        locality_keywords = ["wakad", "baner", "aundh", "ravet", "ghatkopar", "dombivli",
                            "chembur", "mulund", "thane", "andheri", "punawale", "kharadi",
                            "hinjewadi", "viman nagar", "koregaon park", "shivaji nagar"]
        for loc in locality_keywords:
            if loc in query_lower:
                filters["locality"] = loc
                break

        # Budget
        match_budget_range = re.search(
            r'(?:between\s+)?(\d+(?:\.\d+)?)\s*(?:to|-|and)\s*(\d+(?:\.\d+)?)\s*(l|cr|lakh|crore)',
            query_lower
        )
        match_budget_single = re.search(
            r'(?:under|below|less than|upto|up to|within)\s+(\d+(?:\.\d+)?)\s*(l|cr|lakh|crore)',
            query_lower
        )

        def to_inr(amount, unit):
            unit = unit.lower()
            if unit.startswith('l'):
                return float(amount) * 100000
            elif unit.startswith('cr'):
                return float(amount) * 10000000
            return float(amount)

        if match_budget_range:
            low = to_inr(match_budget_range.group(1), match_budget_range.group(3))
            high = to_inr(match_budget_range.group(2), match_budget_range.group(3))
            filters["budget"] = (low, high)
        elif match_budget_single:
            filters["budget"] = to_inr(match_budget_single.group(1), match_budget_single.group(2))

        # Status
        if any(word in query_lower for word in ["ready", "ready to move", "immediate possession"]):
            filters["status"] = "READY_TO_MOVE"
        elif any(word in query_lower for word in ["under construction", "upcoming", "new launch"]):
            filters["status"] = "UNDER_CONSTRUCTION"

        return filters

    def filter_properties(self, filters: Dict, expanded: bool = False) -> pd.DataFrame:
        """Filter properties based on extracted filters."""
        df = self.df.copy()

        if filters["city"] and not self.is_city_available(filters["city"]):
            return pd.DataFrame()

        if 'city' in df.columns:
            df["city"] = df["city"].astype(str).str.strip()
        if 'bhk' in df.columns:
            df["bhk"] = df["bhk"].astype(str).str.upper().str.strip()
        if 'status' in df.columns:
            df["status"] = df["status"].astype(str).str.upper().str.strip()

        filtered = df.copy()

        # Project name filter
        if filters["project_name"]:
            filtered = filtered[filtered["name"].str.lower() == filters["project_name"].lower()]

        # City filter
        city_ids = self.get_city_ids(filters["city"])
        if city_ids and 'city' in filtered.columns:
            filtered = filtered[filtered["city"].isin(city_ids)]

        # BHK filter
        if filters["bhk"] and 'bhk' in filtered.columns:
            filtered = filtered[filtered["bhk"] == filters["bhk"].upper()]

        # Budget filter
        if 'price_inr' in filtered.columns:
            filtered = filtered.dropna(subset=['price_inr'])
            filtered = filtered[filtered['price_inr'] > 0]

            if isinstance(filters["budget"], tuple):
                low, high = filters["budget"]
                filtered = filtered[(filtered["price_inr"] >= low) & (filtered["price_inr"] <= high)]
            elif isinstance(filters["budget"], (int, float)):
                filtered = filtered[filtered["price_inr"] <= filters["budget"]]

        # Status filter (skip if expanded search)
        if filters["status"] and 'status' in filtered.columns and not expanded:
            filtered = filtered[filtered["status"].str.contains(filters["status"], na=False)]

        # Locality filter (skip if expanded search)
        if filters["locality"] and 'address' in filtered.columns and not expanded:
            filtered = filtered[filtered["address"].str.lower().str.contains(filters["locality"], na=False)]

        # Sort by price
        if 'price_inr' in filtered.columns and not filtered.empty:
            filtered = filtered.sort_values('price_inr')

        return filtered.head(10)

    def format_price(self, price: float) -> str:
        """Format price in Indian currency."""
        if pd.isna(price) or price == 0:
            return "Price not available"
        if price >= 10000000:
            return f"₹{price/10000000:.2f} Cr"
        else:
            return f"₹{price/100000:.2f} L"

    def generate_summary(self, results: pd.DataFrame, filters: Dict, expanded_results: pd.DataFrame = None) -> str:
        """Generate summary using ONLY CSV data."""
        requested_city = filters.get("city") or ""
        requested_city = requested_city.capitalize() if requested_city else ""
        
        bhk = filters.get("bhk") or ""
        
        status_raw = filters.get("status")
        status = status_raw.replace("_", " ").lower() if status_raw else "available"
        
        budget = filters.get("budget")
        
        requested_locality = filters.get("locality")
        requested_locality = requested_locality.title() if requested_locality else ""

        if requested_city and not self.is_city_available(requested_city):
            available_cities_str = ", ".join([c.capitalize() for c in self.available_cities])
            return f"⚠️ Sorry, we don't have property listings for **{requested_city}**. Available: **{available_cities_str}**."

        budget_str = ""
        if isinstance(budget, tuple):
            budget_str = f"between {self.format_price(budget[0])} and {self.format_price(budget[1])}"
        elif budget:
            budget_str = f"under {self.format_price(budget)}"

        city_display = requested_city if requested_city else "Mumbai & Pune"

        # No results case
        if results.empty:
            if expanded_results is not None and not expanded_results.empty:
                count = len(expanded_results)
                localities = expanded_results['locality'].value_counts().head(3).index.tolist()
                localities = [loc for loc in localities if loc.lower() != "unknown"]
                locality_str = " and ".join(localities[:2]) if len(localities) >= 2 else localities[0] if localities else "nearby areas"
                
                locality_msg = f" in {requested_locality}" if requested_locality else ""
                return f"❌ No {bhk} {status} properties found{locality_msg} {budget_str}. Expanding to **{locality_str}** found **{count} options**."
            
            locality_msg = f" in {requested_locality}" if requested_locality else ""
            return f"❌ No {bhk} {status} properties found{locality_msg} {budget_str} in {city_display}."

        # Success case - ALL from CSV
        count = len(results)
        localities = results['locality'].value_counts().head(3).index.tolist()
        localities = [loc for loc in localities if loc.lower() != "unknown"]
        locality_str = " and ".join(localities[:2]) if len(localities) >= 2 else localities[0] if localities else "various areas"
        
        top_project = str(results.iloc[0]['name']) if 'name' in results.columns else "Property"
        top_price = results.iloc[0]['price_inr'] if 'price_inr' in results.columns else 0
        min_price = results['price_inr'].min() if 'price_inr' in results.columns else 0
        max_price = results['price_inr'].max() if 'price_inr' in results.columns else 0
        
        status_counts = results['status'].value_counts()
        ready_count = status_counts.get('READY_TO_MOVE', 0)
        construction_count = status_counts.get('UNDER_CONSTRUCTION', 0)

        summary = f"✅ Found **{count} {bhk}** properties in **{city_display}** {budget_str}. "
        summary += f"Located near **{locality_str}**, prices from {self.format_price(min_price)} to {self.format_price(max_price)}. "
        
        if ready_count > 0 and construction_count > 0:
            summary += f"**{ready_count} ready-to-move**, **{construction_count} under construction**. "
        elif ready_count > 0:
            summary += f"All **{ready_count} ready** for possession. "
        elif construction_count > 0:
            summary += f"All **under construction**. "
        
        summary += f"Top: **{top_project}** at {self.format_price(top_price)}."

        return summary

    def process_query(self, query: str) -> Tuple[str, pd.DataFrame, Dict]:
        """Process user query and return results."""
        filters = self.parse_query(query)
        results = self.filter_properties(filters, expanded=False)
        
        expanded_results = None
        if results.empty and (filters["locality"] or filters["status"]):
            expanded_results = self.filter_properties(filters, expanded=True)
        
        summary = self.generate_summary(results, filters, expanded_results)
        final_results = results if not results.empty else (expanded_results if expanded_results is not None else pd.DataFrame())
        
        return summary, final_results, filters
