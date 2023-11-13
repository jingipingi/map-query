import time
import folium
import googlemaps
import pandas as pd
import geopandas as gpd
import branca
import matplotlib.pyplot as plt  # Add this line
import seaborn as sns
import numpy as np
# from matplotlib.colors import rgb2hex


def get_city_info(city_name, api_key):
    gmaps = googlemaps.Client(key=api_key)
    geocode_result = gmaps.geocode(city_name)

    location = geocode_result[0]['geometry']['location']
    northeast = geocode_result[0]['geometry']['viewport']['northeast']
    southwest = geocode_result[0]['geometry']['viewport']['southwest']

    diameter = gmaps.distance_matrix(northeast, southwest)['rows'][0]['elements'][0]['distance']['value']
    radius = diameter / 2

    return location['lat'], location['lng'], radius


def gen_params(city_info, keyword_search):
    return {
        'location': f'{city_info[0]},{city_info[1]}',
        'radius': city_info[2],
        'keyword': keyword_search
    }


def get_all_places(params, city_name, api_key):
    gmaps = googlemaps.Client(key=api_key)
    all_places = pd.DataFrame(columns=['name', 'lat', 'lon', 'category'])
    next_page_token = None

    while True:
        if next_page_token:
            time.sleep(2)
            params['page_token'] = next_page_token

        try:
            places_result = gmaps.places_nearby(**params)
        except Exception as e:
            break
        places = places_result.get('results', [])
        places = [place for place in places_result["results"] if city_name in place["vicinity"]]

        current_places = pd.DataFrame({
            'name': [place['name'] for place in places],
            'lat': [place['geometry']['location']['lat'] for place in places],
            'lon': [place['geometry']['location']['lng'] for place in places],
            'category': params['keyword']
        })

        all_places = pd.concat([all_places, current_places], ignore_index=True, sort=False)
        next_page_token = places_result.get('next_page_token', None)

        if not next_page_token:
            break

    return all_places


# Example usage:

api_key = 'AIzaSyCAsZO05dTX_K5GA_JS_WvsJdgh-3qyDAA'
city_name = 'San Francisco'
city_info = get_city_info(city_name, api_key)
categories = ['Pharmacy', 'Gym','Trader Joes','Safeway','Park', 'Coffee shop']
result_df = pd.DataFrame()

for category in categories:
    initial_params = gen_params(city_info, category)
    cat_df = get_all_places(initial_params, city_name, api_key)
    result_df = pd.concat([result_df, cat_df], ignore_index=True, sort=False)

data = result_df

# Define a color mapping for categories
# Create a function to generate distinct colors for categories
# List of available Folium colors
available_colors = [
    'lightgreen', 'red', 'beige', 'lightgray', 'black', 'pink', 'darkgreen',
    'white', 'purple', 'gray', 'cadetblue', 'darkblue', 'lightblue',
    'lightred', 'darkred', 'orange', 'green', 'blue', 'darkpurple'
]

m = folium.Map(location=[city_info[0], city_info[1]], zoom_start=12)

# Create a dictionary to store category colors
category_colors = {}

# Iterate through the DataFrame and add markers with assigned colors
for index, row in result_df.iterrows():
    category = row['category']

    if category not in category_colors:
        # Assign the next color in the shuffled list to the category
        category_colors[category] = available_colors[len(category_colors)]

    color = category_colors[category]

    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=row['name'],
        icon=folium.Icon(color=color)
    ).add_to(m)

#TODO: color neighborhood regions by median rental price for a 2b1b
'https://api.bridgedataoutput.com/api/v2/zgecon/{endpoint}?access_token={access_token}&metadataType={metadata}'

# Load neighborhood boundary GeoJSON data from the JSON file
neighborhoods_json = "SanFrancisco.Neighborhoods.json"
neighborhoods_gdf = gpd.read_file(neighborhoods_json)

# Read rent values from a CSV file
rent_data = pd.read_csv("neighborhood_rent.csv")  # Replace with the actual file path

# Merge rent data with neighborhood geometries
merged_data = neighborhoods_gdf.merge(rent_data, on="neighborhood", how="left")
print(merged_data)

cp = folium.Choropleth(
    geo_data = neighborhoods_json,
    name ='choropleth',
    data = merged_data,
    columns = ['neighborhood','rent'],
    key_on='feature.properties.neighborhood',
    fill_color = 'YlGnBu',     #I passed colors Yellow,Green,Blue
    fill_opacity = 0.7,
    line_opacity = 0.2,
   legend_name = "Rent Index"
).add_to(m)

# Iterate through each neighborhood feature and add it to the map with a Popup label and color based on rent
for idx, row in merged_data.iterrows():
    neighborhood_name = row["neighborhood"]
    neighborhood_geometry = row["geometry"]
    rent_value = row["rent"]
    print(rent_value)

    # Create a GeoJson object with a Popup label and custom style
    folium.GeoJson(
        neighborhood_geometry,
        name=neighborhood_name
    ).add_child(folium.Popup('name: ' + neighborhood_name + ', rent: ' + str(rent_value))).add_to(m)

#TODO: filter the results to be confined to the city that was searched

# Display the map
m.save("interactive_map.html")