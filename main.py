import time
import folium
import googlemaps
import pandas as pd


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


def get_all_places(params, api_key):
    gmaps = googlemaps.Client(key=api_key)
    all_places = pd.DataFrame(columns=['name', 'lat', 'lon', 'category'])
    next_page_token = None

    while True:
        if next_page_token:
            time.sleep(2)
            params['page_token'] = next_page_token

        try:
            print("params: ", params)
            places_result = gmaps.places_nearby(**params)
        except Exception as e:
            print("error: ", e)
            break
        places = places_result.get('results', [])

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
city_info = get_city_info('San Francisco', api_key)
categories = ['Pharmacy', 'Gym','Trader Joes','Safeway','Park']
result_df = pd.DataFrame()

for category in categories:
    initial_params = gen_params(city_info, category)
    cat_df = get_all_places(initial_params, api_key)
    result_df = pd.concat([result_df, cat_df], ignore_index=True, sort=False)
    print(result_df)

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
#TODO: filter the results to be confined to the city that was searched

# Display the map
m.save("interactive_map.html")