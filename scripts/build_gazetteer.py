#!/usr/bin/env python3
"""Historical gazetteer for the trade-origins map. Labels in the UK Annual
Statement are the country/region whence goods were CONSIGNED (shipped), not
where they were produced, so each is placed at its PRINCIPAL PORT OF SHIPMENT
to the UK rather than a geographic centroid (United States -> New York, Canada
-> Montreal, Germany -> Hamburg, Austria-Hungary -> Trieste). Every choice is
documented in `note`.

kind: country | colony | port | region | coast | aggregate
  aggregate with lat/lon null = residual bucket shown as an unmapped total.
  parent links a child to its umbrella; children lists the constituents.
"""
import json
from pathlib import Path

G = {}
def add(label, lat, lon, kind, note='', parent=None, children=None):
    G[label] = {'lat': lat, 'lon': lon, 'kind': kind, 'note': note,
                'parent': parent, 'children': children or []}

# ---- Europe (principal shipment ports) ----
add('France', 49.49, 0.11, 'country', 'principal consignment via Le Havre (also Bordeaux/Marseille)')
add('Germany', 53.55, 9.99, 'country', 'German Empire; consignment via Hamburg (also Bremen)')
add('Holland', 51.92, 4.48, 'country', 'Netherlands; Rotterdam/Amsterdam entrepot — much is re-consignment, not Dutch production')
add('Belgium', 51.22, 4.40, 'country', 'Antwerp entrepot — substantially transit trade')
add('Italy', 44.41, 8.93, 'country', 'consignment via Genoa (also Leghorn/Naples)')
add('Spain', 43.26, -2.93, 'country', 'placed at Bilbao (iron ore); Spanish trade also ships from Seville/Valencia/Malaga')
add('Portugal', 38.72, -9.13, 'country', 'Lisbon (also Oporto)')
add('Portugal, Azores, And Madeira', 38.72, -9.13, 'country', 'Portugal incl. its Atlantic islands (Azores, Madeira)')
add('Russia', 59.94, 30.31, 'country', 'Russian Empire; placed at St Petersburg (Baltic)')
add('Russia (Northern Ports)', 59.94, 30.31, 'coast', 'Baltic shipping — St Petersburg/Riga/Kronstadt', parent='Russia')
add('Russia (Southern Ports)', 46.48, 30.73, 'coast', 'Black Sea shipping — Odessa', parent='Russia')
add('Denmark', 55.68, 12.57, 'country', 'Copenhagen')
add('Sweden', 57.71, 11.97, 'country', 'consignment via Gothenburg')
add('Norway', 59.91, 10.75, 'country', 'Christiania (Oslo); also Bergen')
add('Sweden And Norway', 58.8, 11.3, 'aggregate', 'union of Sweden and Norway (1814-1905); pre-split combined line', children=['Sweden','Norway'])
add('Greece', 37.94, 23.65, 'country', 'Piraeus (Athens)')
add('Roumania', 45.43, 28.05, 'country', 'Romania; Danube grain via Galati/Braila')
add('Austrian Territories', 45.65, 13.77, 'country', 'Austria-Hungary (Habsburg Empire); Adriatic consignment via Trieste/Fiume')
add('Turkey', 41.01, 28.98, 'country', 'Ottoman Empire; consignment via Constantinople/Smyrna')
add('Turkey Proper', 41.01, 28.98, 'country', 'Ottoman core, distinct from Ottoman dependencies', parent='Turkey')
add('Channel Islands', 49.45, -2.35, 'region', 'Jersey/Guernsey — Crown dependencies')
add('Malta', 35.90, 14.51, 'colony', 'British Mediterranean coaling/entrepot station (Valletta)')
add('Gibraltar', 36.14, -5.35, 'colony', 'British entrepot at the strait — mostly transit trade')

# ---- Americas ----
add('United States Of America', 40.71, -74.01, 'country', 'placed at New York (dominant Atlantic shipment port)')
add('United States Of America (Atlantic)', 40.71, -74.01, 'coast', 'US goods shipped from Atlantic ports — New York etc.', parent='United States Of America')
add('United States Of America (Pacific)', 37.77, -122.42, 'coast', 'US goods shipped from Pacific ports — San Francisco', parent='United States Of America')
add('United States Of America (Atlantic & Pacific)', 40.71, -74.01, 'coast', 'combined coast line', parent='United States Of America')
add('Canada', 45.50, -73.57, 'colony', 'British North America / Dominion of Canada; placed at Montreal (St Lawrence grain/timber)')
add('Brazil', -22.91, -43.17, 'country', 'Rio de Janeiro (also Santos for coffee)')
add('Argentine Republic', -34.61, -58.38, 'country', 'Argentina; Buenos Aires')
add('Chili', -33.05, -71.61, 'country', 'Chile (period spelling); Valparaiso')
add('Chile', -33.05, -71.61, 'country', 'Valparaiso')
add('Peru', -12.05, -77.14, 'country', 'Callao / Lima')
add('Uruguay', -34.90, -56.19, 'country', 'Montevideo')
add('United States Of Colombia', 10.40, -75.51, 'country', 'historical federal name for Colombia (to 1886); placed at Cartagena')
add('United States Of Colombia (Newgranada', 10.40, -75.51, 'country', 'OCR-garbled "New Granada" tail; = Colombia', parent='United States Of Colombia')
add('Venezuela', 10.60, -66.93, 'country', 'La Guaira (Caracas)')
add('Mexico', 19.20, -96.14, 'country', 'Veracruz')
add('Central America', 13.0, -85.0, 'region', 'isthmus states as a printed group')
add('Cuba', 23.11, -82.37, 'colony', 'Spanish Cuba; Havana')
add('British Guiana', 6.80, -58.16, 'colony', 'Georgetown (Demerara)')
add('British West India Islands', 15.0, -75.0, 'aggregate', 'British Caribbean colonies as one line', children=['Jamaica','Trinidad','Barbados'])
add('Spanish West India Islands', 20.0, -77.0, 'aggregate', 'Cuba + Puerto Rico')
add('Foreign West Indies', 16.0, -73.0, 'aggregate', 'non-British Caribbean')

# ---- Asia ----
add('British East Indies', 20.0, 77.0, 'aggregate', 'colonial umbrella for British India (Bombay/Madras/Bengal presidencies) and sometimes the Straits & Ceylon; placed inland as an aggregate', children=['Bombay','Madras','Bengal','Bengal And Burmah','Straits Settlements','Ceylon'])
add('British India', 20.0, 77.0, 'aggregate', 'British India as one line', children=['Bombay','Madras','Bengal','Bengal And Burmah'])
add('Bombay', 18.96, 72.82, 'port', 'Bombay Presidency port (incl. Scinde/Karachi to ~1890)', parent='British East Indies')
add('Madras', 13.08, 80.29, 'port', 'Madras Presidency port', parent='British East Indies')
add('Bengal', 22.57, 88.36, 'port', 'Calcutta (Bengal Presidency)', parent='British East Indies')
add('Bengal And Burmah', 20.5, 90.5, 'port', 'Bengal Presidency incl. British Burma (pre-separation)', parent='British East Indies')
add('Burmah', 16.77, 96.16, 'colony', 'British Burma; Rangoon', parent='British East Indies')
add('Ceylon', 6.93, 79.85, 'colony', 'Colombo — tea/coffee', parent='British East Indies')
add('Straits Settlements', 1.29, 103.85, 'colony', 'Singapore/Penang/Malacca entrepot', parent='British East Indies')
add('China', 31.23, 121.47, 'country', 'placed at Shanghai; scope varies by era (pre-1885 "China and Hong Kong")')
add('Hong Kong', 22.30, 114.17, 'colony', 'British free port; largely transit trade for South China', parent='China')
add('Japan', 35.44, 139.64, 'country', 'Yokohama')
add('Java', -6.20, 106.85, 'colony', 'Dutch East Indies; Batavia (Jakarta) — sugar/coffee')
add('Philippine Islands', 14.60, 120.98, 'colony', 'Spanish Philippines; Manila')
add('Philippine And Ladrone Islands', 14.60, 120.98, 'colony', 'Philippines + Ladrones (Marianas/Guam)', parent='Philippine Islands')
add('Aden', 12.79, 45.03, 'port', 'British coaling station / Red Sea entrepot')
add('Asiatic', 30.0, 70.0, 'region', 'unspecified Asiatic origins as a printed group')

# ---- Africa ----
add('Egypt', 31.20, 29.92, 'country', 'cotton via Alexandria (British-occupied from 1882)')
add('Algeria', 36.75, 3.06, 'colony', 'French Algeria; Algiers')
add('Morocco', 35.78, -5.81, 'country', 'Tangier')
add('British Possessions In South Africa', -32.0, 24.0, 'aggregate', 'Cape Colony + Natal (wool); pre-1891 combined line, later split', children=['Cape Of Good Hope','Natal'])
add('Cape Of Good Hope', -33.92, 18.42, 'colony', 'Cape Town (Cape Colony)', parent='British Possessions In South Africa')
add('Natal', -29.88, 31.05, 'colony', 'Durban', parent='British Possessions In South Africa')
add('Mauritius', -20.16, 57.50, 'colony', 'Port Louis — British sugar colony')
add('Lagos', 6.45, 3.39, 'colony', 'British West Africa — palm oil')
add('Western Africa (Foreign', 5.55, -0.20, 'region', 'non-British West African coast (OCR-truncated); placed at Accra')
add('West Africa Portuguese Possessions Not Particularly Design Nated', -8.84, 13.23, 'colony', 'Portuguese West Africa (Angola); Luanda; OCR-garbled label')

# ---- Australasia (capital ports) ----
add('Australasia', -30.0, 145.0, 'aggregate', 'umbrella for the Australian colonies + New Zealand', children=['New South Wales','Victoria','Queensland','South Australia','Western Australia','Tasmania','New Zealand'])
add('Australia', -30.0, 140.0, 'aggregate', 'Australian colonies collectively (pre-Federation)', children=['New South Wales','Victoria','Queensland','South Australia','Western Australia','Tasmania'])
add('New South Wales', -33.87, 151.21, 'colony', 'Sydney', parent='Australasia')
add('Victoria', -37.81, 144.96, 'colony', 'Melbourne', parent='Australasia')
add('Queensland', -27.47, 153.03, 'colony', 'Brisbane', parent='Australasia')
add('South Australia', -34.93, 138.60, 'colony', 'Adelaide', parent='Australasia')
add('Western Australia', -32.06, 115.74, 'colony', 'Fremantle (Perth)', parent='Australasia')
add('Tasmania', -42.88, 147.33, 'colony', 'Hobart', parent='Australasia')
add('New Zealand', -41.29, 174.78, 'colony', 'Wellington', parent='Australasia')

# ---- second wave: real recurring origins surfaced by the residual audit ----
add('Canary Islands', 28.10, -15.42, 'region', 'Spanish Atlantic islands; Las Palmas (bananas, tomatoes)')
add('Ecuador', -2.19, -79.88, 'country', 'Guayaquil (cocoa)')
add('Persia', 28.98, 50.84, 'country', 'consignment via the Persian Gulf (Bushire)')
add('Newfoundland', 47.56, -52.71, 'colony', 'British; St John\'s (dried cod)')
add('British Honduras', 17.50, -88.20, 'colony', 'Belize (mahogany, logwood)')
add('Sierra Leone', 8.48, -13.23, 'colony', 'British West Africa; Freetown')
add('The Gold Coast', 5.55, -0.20, 'colony', 'British West Africa; Accra (palm oil, later cocoa)')
add('Gambia', 13.45, -16.58, 'colony', 'British West Africa; Bathurst (groundnuts)')
add('Niger Protectorate', 4.75, 7.00, 'colony', 'Niger delta / Oil Rivers, British West Africa (palm oil)')
add('Fernando Po', 3.75, 8.78, 'colony', 'Gulf of Guinea island (Bioko)')
add('Madagascar', -18.15, 49.41, 'country', 'Tamatave (Toamasina)')
add('Zanzibar And Pemba', -6.16, 39.19, 'colony', 'East African entrepot; cloves, ivory')
add('Congo Free State', -5.85, 13.06, 'country', 'Boma / lower Congo (rubber, ivory)')
add('Tripoli', 32.90, 13.19, 'region', 'Ottoman North Africa (Libya)')
add('Tunis', 36.80, 10.18, 'country', 'Tunisia (French protectorate from 1881)')
add('Siam', 13.75, 100.50, 'country', 'Thailand; Bangkok (rice)')
add('Cyprus', 35.10, 33.40, 'colony', 'British from 1878; Larnaca')
add('Dutch Guiana', 5.87, -55.17, 'colony', 'Surinam; Paramaribo')
add('Danish West India Islands', 17.74, -64.70, 'colony', 'St Croix / St Thomas (Danish, sugar)')
add('Dutch West India Islands', 12.11, -68.93, 'colony', 'Curacao (Dutch)')
add('Hayti And St Domingo', 18.54, -72.34, 'country', 'Hispaniola — Haiti + Santo Domingo (coffee)')
add('Falkland Islands', -51.70, -57.85, 'colony', 'British South Atlantic (wool)')
add('Bolivia', -17.78, -63.18, 'country', 'consignment via the Pacific coast (silver, tin)')
add('Nicaragua', 12.15, -86.27, 'country', 'Corinto (coffee)')
add('Costa Rica', 9.98, -83.03, 'country', 'Puerto Limon (coffee, bananas)')
add('Bulgaria', 43.20, 27.91, 'country', 'Black Sea; Varna (grain)')
add('Bermudas', 32.29, -64.78, 'colony', 'British North Atlantic')

# ---- residual aggregates (no single port: shown as unmapped total) ----
for lbl, note in [
    ('Other Countries', 'residual "all other" foreign origins'),
    ('Other Foreign Countries', 'residual foreign origins'),
    ('Other British Possessions', 'residual British colonial origins'),
    ('Other Parts', 'residual'),
    ('Other', 'residual')]:
    G[lbl] = {'lat': None, 'lon': None, 'kind': 'aggregate', 'note': note,
              'parent': None, 'children': []}

out = Path('reference/map_gazetteer.json')
out.write_text(json.dumps(G, ensure_ascii=False, indent=1))
mapped = sum(1 for v in G.values() if v['lat'] is not None)
print(f'gazetteer: {len(G)} labels ({mapped} at ports, {len(G)-mapped} residual) -> {out}')
