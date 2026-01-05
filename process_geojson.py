import json
import math
import os

# Configuration
INPUT_FILE = 'assets/data/japan.geojson'
OUTPUT_FILE = 'assets/js/japan-map.js'
DOT_SPACING = 2.0 # Finer dots for Overview to capture Aomori
DETAIL_SPACING = 1.5 # Even finer for Zoom
SVG_WIDTH = 800 
SVG_HEIGHT = 900 # Reduced from 1050 to trim bottom whitespace

# Region Mapping (Same as before)
REGION_MAP = {
    1: 'Hokkaido',
    2: 'Tohoku', 3: 'Tohoku', 4: 'Tohoku', 5: 'Tohoku', 6: 'Tohoku', 7: 'Tohoku',
    8: 'Kanto', 9: 'Kanto', 10: 'Kanto', 11: 'Kanto', 12: 'Kanto', 13: 'Kanto', 14: 'Kanto',
    15: 'Chubu', 16: 'Chubu', 17: 'Chubu', 18: 'Chubu', 19: 'Chubu', 20: 'Chubu', 21: 'Chubu', 22: 'Chubu', 23: 'Chubu',
    24: 'Kansai', 25: 'Kansai', 26: 'Kansai', 27: 'Kansai', 28: 'Kansai', 29: 'Kansai', 30: 'Kansai',
    31: 'Chugoku', 32: 'Chugoku', 33: 'Chugoku', 34: 'Chugoku', 35: 'Chugoku',
    36: 'Shikoku', 37: 'Shikoku', 38: 'Shikoku', 39: 'Shikoku',
    40: 'Kyushu', 41: 'Kyushu', 42: 'Kyushu', 43: 'Kyushu', 44: 'Kyushu', 45: 'Kyushu', 46: 'Kyushu',
    47: 'Okinawa'
}

NAME_JA_MAP = {
    'Hokkaido': '北海道', 'Tohoku': '東北', 'Kanto': '関東', 'Chubu': '中部', 'Kansai': '関西',
    'Chugoku': '中国', 'Shikoku': '四国', 'Kyushu': '九州', 'Okinawa': '沖縄'
}

# Color Rotation Palette (using region variable names from CSS)
# We will map prefectures to a specific "color class" index (0-8)
# to reuse the 8 region colors cyclically/randomly for distinctness.
COLOR_CLASSES = [
    'hokkaido', 'tohoku', 'kanto', 'chubu', 'kansai', 'chugoku', 'shikoku', 'kyushu', 'okinawa'
]

def load_geojson(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def mercator_projection(lon, lat):
    # Simplified Mercator (Radians)
    x = math.radians(lon)
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y

def get_bounds(features):
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    for feature in features:
        geom = feature['geometry']
        coords = geom['coordinates']
        
        def flatten(lst):
            for item in lst:
                if isinstance(item[0], (int, float)):
                    yield item
                else:
                    yield from flatten(item)
                    
        for lon, lat in flatten(coords):
            x, y = mercator_projection(lon, lat)
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
            
    return min_x, min_y, max_x, max_y

def point_in_polygon(x, y, poly_points):
    inside = False
    j = len(poly_points) - 1
    for i in range(len(poly_points)):
        xi, yi = poly_points[i]
        xj, yj = poly_points[j]
        
        intersect = ((yi > y) != (yj > y)) and \
            (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
        if intersect:
            inside = not inside
        j = i
    return inside

def get_hokkaido_subregion(lat, lon):
    # Approximate split
    # Sapporo (Doo) is ~ 141.35, 43.06
    # Asahikawa (Dohoku/Doo border) ~ 142.3, 43.7
    # Hakodate (Donan) ~ 140.7, 41.7
    # Kushiro (Doto) ~ 144.4, 43.0
    
    if lat < 42.5:
        return '道南' # Donan (South)
    elif lon > 143.0:
        return '道東' # Doto (East)
    elif lat > 44.0:
        return '道北' # Dohoku (North)
    else:
        return '道央' # Doo (Central)

def generate_dots(features, bounds, scale, offsets, spacing, is_detail=False):
    min_mex, min_mey, max_mex, max_mey = bounds
    offset_x, offset_y = offsets
    # Use global SVG_HEIGHT defined at module level
    
    dots = []
    
    # ...
    # Shift map down by adding to offset_y or modifying sy
    # sy = SVG_HEIGHT - ((my - min_mey) * scale + offset_y)
    # To move DRAWING down (higher sy), we need smaller Y term or post-add
    # Let's add a fixed pixel offset
    GLOBAL_OFFSET_Y = 0  # Shift down by 40px
    
    def geo_to_svg(lon, lat):
        mx, my = mercator_projection(lon, lat)
        sx = (mx - min_mex) * scale + offset_x
        # Normal calc
        sy = SVG_HEIGHT - ((my - min_mey) * scale + offset_y)
        # Shift down
        return sx, sy + GLOBAL_OFFSET_Y
        
    def svg_to_geo(sx, sy):
         # Reverse with offset
         # sy_shifted = sy - GLOBAL_OFFSET_Y
         sy_shifted = sy - GLOBAL_OFFSET_Y
         
         my = ((SVG_HEIGHT - sy_shifted) - offset_y) / scale + min_mey
         mx = (sx - offset_x) / scale + min_mex
         
         lon = math.degrees(mx)
         lat = math.degrees(2 * (math.atan(math.exp(my)) - math.pi / 4))
         lat = math.degrees(2 * (math.atan(math.exp(my)) - math.pi / 4))
         return lon, lat

    for feature in features:
        props = feature['properties']
        pref_id = props.get('id')
        if not pref_id: continue
        
        region = REGION_MAP.get(pref_id, 'Unknown')
        pref_name = props.get('nam_ja', '')
        
        geom = feature['geometry']
        if geom['type'] == 'Polygon':
            polys = [geom['coordinates']]
        elif geom['type'] == 'MultiPolygon':
            polys = geom['coordinates']
        else:
            continue
            
        for poly in polys:
            outer_ring = poly[0]
            svg_ring = [geo_to_svg(p[0], p[1]) for p in outer_ring]
            
            rmin_x = min(p[0] for p in svg_ring)
            rmax_x = max(p[0] for p in svg_ring)
            rmin_y = min(p[1] for p in svg_ring)
            rmax_y = max(p[1] for p in svg_ring)
            
            start_x = math.floor(rmin_x / spacing) * spacing
            end_x = math.ceil(rmax_x / spacing) * spacing
            start_y = math.floor(rmin_y / spacing) * spacing
            end_y = math.ceil(rmax_y / spacing) * spacing
            
            # Generate grid points with float spacing
            current_y = start_y
            while current_y <= end_y:
                current_x = start_x
                while current_x <= end_x:
                    px = current_x
                    py = current_y
                    
                    if point_in_polygon(px, py, svg_ring):
                        # Radius logic
                        radius = (spacing / 2.0) * 0.8
                        
                        # Color/Name logic
                        display_name = pref_name
                        color_class_suffix = COLOR_CLASSES[pref_id % len(COLOR_CLASSES)]
                        
                        if pref_id == 1:
                            lon, lat = svg_to_geo(px, py)
                            subregion = get_hokkaido_subregion(lat, lon)
                            # display_name = subregion
                            # Subregion colors
                            sub_map = {'道南': 0, '道央': 1, '道北': 2, '道東': 3}
                            color_class_suffix = COLOR_CLASSES[sub_map.get(subregion, 0)]
                        
                        dots.append({
                            'x': round(px, 1),
                            'y': round(py, 1),
                            'r': round(radius, 2),
                            'region': region,
                            'name': display_name,
                            'color': color_class_suffix
                        })
                    
                    current_x += spacing
                current_y += spacing
    return dots

def main():
    print("Loading GeoJSON...")
    data = load_geojson(INPUT_FILE)
    features = data['features']
    
    print("Calculating bounds...")
    bounds = get_bounds(features)
    min_mex, min_mey, max_mex, max_mey = bounds
    
    geo_width = max_mex - min_mex
    geo_height = max_mey - min_mey
    
    scale_x = SVG_WIDTH / geo_width
    scale_y = SVG_HEIGHT / geo_height
    scale = min(scale_x, scale_y) * 0.9
    
    offset_x = (SVG_WIDTH - (geo_width * scale)) / 2
    offset_y = (SVG_HEIGHT - (geo_height * scale)) / 2
    offsets = (offset_x, offset_y)
    
    # 1. Overview: Dense enough to capture Aomori
    print(f"Generating Overview Dots (Spacing {DOT_SPACING})...") 
    overview_dots = generate_dots(features, bounds, scale, offsets, DOT_SPACING, is_detail=False)
    print(f"Overview Count: {len(overview_dots)}")
    
    # 2. Detail: High res
    print(f"Generating Detail Dots (Spacing {DETAIL_SPACING})...") 
    all_detail_dots = generate_dots(features, bounds, scale, offsets, DETAIL_SPACING, is_detail=True)
    
    detail_dots_by_region = {}
    for dot in all_detail_dots:
        r = dot['region']
        if r not in detail_dots_by_region:
            detail_dots_by_region[r] = []
        detail_dots_by_region[r].append(dot)
    
    map_data = {
        'overview': overview_dots,
        'regions': detail_dots_by_region
    }
    
    js_content = f"""// Japan Map Dot Pattern Generator (GeoJSON Source - Multi-Res + Region Colors + Single Dot + Popup)
document.addEventListener('DOMContentLoaded', () => {{
    initMap();
}});

// Initialize modal handlers after a short delay to ensure DOM is ready
setTimeout(() => {{
    if (document.getElementById('event-modal')) {{
        setupModal();
    }}
}}, 100);

// Global debug for status
window.debugPrefStatus = true;

let currentMapData = null;
const EVENT_DATA_REF = typeof EVENT_DATA !== 'undefined' ? EVENT_DATA : {{ visited: [], wishlist: [] }};

const MAP_CONFIG = {{
    minMex: {min_mex},
    minMey: {min_mey},
    scale: {scale},
    offsetX: {offset_x},
    offsetY: {offset_y},
    svgHeight: {SVG_HEIGHT}
}};

function svgToGeo(sx, sy) {{
     const my = ((MAP_CONFIG.svgHeight - sy) - MAP_CONFIG.offsetY) / MAP_CONFIG.scale + MAP_CONFIG.minMey;
     const mx = (sx - MAP_CONFIG.offsetX) / MAP_CONFIG.scale + MAP_CONFIG.minMex;
     const lon = mx * 180 / Math.PI;
     const lat = 2 * (Math.atan(Math.exp(my)) - Math.PI / 4) * 180 / Math.PI;
     return {{ lat, lon }};
}}

function mapEventsToDots(dots) {{
    const allEvents = [
        ...EVENT_DATA_REF.visited.map(e => ({{...e, status: 'visited'}})),
        ...EVENT_DATA_REF.wishlist.map(e => ({{...e, status: 'wishlist'}}))
    ];
    
    dots.forEach(d => d.events = []);

    const MAX_DIST_SQ = 0.05; // Approx 0.22 deg (~25km) squared. Prevents cross-region assignment.

    allEvents.forEach(e => {{
        if (!e.lat || !e.lon) return;
        
        let nearest = null;
        let minD = Infinity;
        
        dots.forEach(dot => {{
             // Strict Prefecture Check: Event must belong to this dot's prefecture
             // e.prefecture (e.g. "香川県") must include dot.name (e.g. "香川")
             if (!dot.name || e.prefecture.indexOf(dot.name) === -1) return;

             const geo = svgToGeo(dot.x, dot.y);
             const d = (geo.lat - e.lat)**2 + (geo.lon - e.lon)**2;
             if (d < minD) {{
                 minD = d;
                 nearest = dot;
             }}
        }});
        
        // Only assign if within reasonable distance (prevents Osaka event showing on Kanto map)
        if (nearest && minD < MAX_DIST_SQ) {{
            if (!nearest.events) nearest.events = [];
            nearest.events.push(e);
        }}
    }});
}}

function initMap() {{
    const mapSvg = document.getElementById('japan-map');
    if (!mapSvg) return;
    
    currentMapData = {json.dumps(map_data, ensure_ascii=False)};
    
    mapEventsToDots(currentMapData.overview);
    Object.values(currentMapData.regions).forEach(dots => mapEventsToDots(dots));
    
    renderDots(currentMapData.overview, false);
    renderOverviewLabels();
    
    // Setup reset button
    const resetBtn = document.getElementById('reset-zoom');
    if (resetBtn) {{
        resetBtn.onclick = () => {{
            resetZoom();
        }};
    }}
    
    // Background click to reset
    document.addEventListener('click', (e) => {{
        const mapSvg = document.getElementById('japan-map');
        const modal = document.getElementById('event-modal');
        
        // Ignore if modal is open
        if (modal && modal.style.display === 'block') return;
        
        // If clicking SVG or Container directly (background)
        // Note: Dots/Labels have stopPropagation() so they won't trigger this
        if (e.target === mapSvg || e.target.closest('.map-container') && !e.target.closest('.prefecture') && !e.target.closest('.label-text') && !e.target.closest('.label-line')) {{
             const resetBtn = document.getElementById('reset-zoom');
             if (resetBtn && resetBtn.style.display !== 'none') {{
                 resetZoom();
             }}
        }}
    }});
}}

function renderDots(dots, usePrefColor) {{
    const mapSvg = document.getElementById('japan-map');
    mapSvg.innerHTML = '';
    
    const frag = document.createDocumentFragment();
    
    dots.forEach(dot => {{
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', dot.x);
        circle.setAttribute('cy', dot.y);
        circle.setAttribute('r', dot.r);
        
        // Extended Region Logic (Restored)
        let className = 'prefecture';
        if (usePrefColor) {{
            // Use the specific color class assigned in Python
            className += ` region-${{dot.color}}`;
        }} else {{
            // Use standard region class
            className += ` region-${{dot.region.toLowerCase()}}`;
        }}
        
        // 1. Prefecture Status
        if (typeof getPrefectureStatus === 'function') {{
             const status = getPrefectureStatus(dot.name);
             if (window.debugPrefStatus) console.log('PrefStatus:', dot.name, status);
             if (status === 'visited') {{
                 className += ' prefecture-visited';
             }} else if (status === 'wishlist') {{
                 className += ' prefecture-wishlist';
             }}
        }}

        // 2. Spot Status & Interaction
        if (dot.events && dot.events.length > 0) {{
            const hasVisited = dot.events.some(e => e.status === 'visited');
            className += hasVisited ? ' spot-visited' : ' spot-wishlist';
            
            circle.addEventListener('click', (e) => {{
                e.stopPropagation();
                openModal(dot.events);
            }});
        }} else {{
            circle.addEventListener('click', (e) => {{
                e.stopPropagation();
                zoomToRegion(dot.region);
            }});
        }}
        
        circle.setAttribute('class', className);
        circle.setAttribute('data-name', dot.name);
        circle.setAttribute('data-region', dot.region);
        
        // Tooltip: Show Event Name inside
        circle.addEventListener('mouseenter', (e) => {{
            let tooltipText = dot.name;
            if (dot.events && dot.events.length > 0) {{
                 const status = dot.events.some(ev => ev.status === 'visited') ? '参加済み' : 'いつか参加したい';
                 // Format: "Prefecture | EventName (Status)" or just EventName
                 // User said: "In the speech bubble... display event name"
                 tooltipText = `${{dot.name}} | ${{dot.events[0].name}} (${{status}})`;
                 if (dot.events.length > 1) tooltipText += ' +';
            }}
            showTooltip(e, tooltipText);
        }});
        
        circle.addEventListener('mouseleave', hideTooltip);
        
        frag.appendChild(circle);
    }});
    
    mapSvg.appendChild(frag);
}}

function zoomToRegion(regionName) {{
    const mapSvg = document.getElementById('japan-map');
    const regionDots = currentMapData.regions[regionName];
    if (!regionDots || regionDots.length === 0) return;
    
    renderDots(regionDots, true);
    renderZoomLabels(regionDots, regionName); // Show annotations
    
    // Remove Overview Labels
    const ovLabels = document.getElementById('overview-labels');
    if (ovLabels) ovLabels.remove();
    
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    regionDots.forEach(dot => {{
        if (dot.x < minX) minX = dot.x;
        if (dot.y < minY) minY = dot.y;
        if (dot.x > maxX) maxX = dot.x;
        if (dot.y > maxY) maxY = dot.y;
    }});
    
    // Adjusted padding for larger view (Hokkaido/Okinawa)
    let padding = 20;
    if (regionName === 'Okinawa') padding = 40;

    const width = maxX - minX + (padding * 2);
    const height = maxY - minY + (padding * 2);
    const viewBox = `${{minX - padding}} ${{minY - padding}} ${{width}} ${{height}}`;
    
    mapSvg.style.transition = 'all 0.8s cubic-bezier(0.25, 1, 0.5, 1)';
    mapSvg.setAttribute('viewBox', viewBox);
    
    document.getElementById('reset-zoom').style.display = 'block';
}}

function renderZoomLabels(regionDots, regionName) {{
    const mapSvg = document.getElementById('japan-map');
    let group = document.getElementById('zoom-labels');
    if (group) group.remove();
    
    group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    group.id = 'zoom-labels';
    
    // Get all event dots and sort by Y
    const eventDots = regionDots.filter(d => d.events && d.events.length > 0);
    eventDots.sort((a, b) => a.y - b.y);

    const lineHeight = 7;
    let lastRightBottom = -Infinity;
    let lastLeftBottom = -Infinity;

    eventDots.forEach(dot => {{
        const config = dot.events[0].labelConfig;
        let labelX, labelY;
        
        if (config && config.angle !== undefined && config.length !== undefined) {{
            // Manual positioning
            const rad = config.angle * Math.PI / 180;
            labelX = dot.x + config.length * Math.cos(rad);
            labelY = dot.y + config.length * Math.sin(rad);
        }} else {{
            // Auto positioning based on labelSide
            const isLeftSide = dot.events[0].labelSide === 'left';
            const offX = isLeftSide ? -30 : 30;
            labelY = dot.y;
            
            if (isLeftSide) {{
                if (labelY < lastLeftBottom + lineHeight) {{
                    labelY = lastLeftBottom + lineHeight;
                }}
                lastLeftBottom = labelY;
            }} else {{
                if (labelY < lastRightBottom + lineHeight) {{
                    labelY = lastRightBottom + lineHeight;
                }}
                lastRightBottom = labelY;
            }}
            
            labelX = dot.x + offX;
        }}
        
        // Draw line
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', dot.x);
        line.setAttribute('y1', dot.y);
        line.setAttribute('x2', labelX);
        line.setAttribute('y2', labelY - 3);
        line.setAttribute('class', 'label-line');
        group.appendChild(line);
        
        // Draw text with dynamic anchor
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        const isLeft = labelX < dot.x;
        
        text.setAttribute('x', isLeft ? labelX - 5 : labelX + 5);
        text.setAttribute('y', labelY + 1);
        text.setAttribute('class', 'label-text region-' + regionName);
        text.setAttribute('dominant-baseline', 'middle');
        text.setAttribute('text-anchor', isLeft ? 'end' : 'start');
        
        let labelContent = dot.events[0].name;
        if (dot.events.length > 1) labelContent += ` (+${{dot.events.length - 1}})`;
        text.textContent = labelContent;
        
        text.onclick = (e) => {{
            e.stopPropagation();
            window.openEventModal(dot.events);
        }};
        group.appendChild(text);
    }});
    
    mapSvg.appendChild(group);
}}

function renderOverviewLabels() {{
    const mapSvg = document.getElementById('japan-map');
    let group = document.getElementById('overview-labels');
    if (group) group.remove();
    
    const eventDots = currentMapData.overview.filter(d => d.events && d.events.length > 0);
    if (eventDots.length === 0) return;

    group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    group.id = 'overview-labels';
    group.classList.add('fade-in-labels');

    // 1. Group by Prefecture to find Centers
    const prefGroups = {{}};
    eventDots.forEach(d => {{
        if (!prefGroups[d.name]) prefGroups[d.name] = [];
        prefGroups[d.name].push(d);
    }});
    
    let labels = [];
    Object.keys(prefGroups).forEach(prefName => {{
        const dots = prefGroups[prefName];
        const centerX = dots.reduce((sum, d) => sum + d.x, 0) / dots.length;
        const centerY = dots.reduce((sum, d) => sum + d.y, 0) / dots.length;
        const allEvents = dots.flatMap(d => d.events);
        
        labels.push({{
            name: prefName,
            count: allEvents.length,
            events: allEvents,
            x: centerX,
            y: centerY,
            region: dots[0].region
        }});
    }});

    // 2. Sort by Y to process from top to bottom
    labels.sort((a, b) => a.y - b.y);

    let lastLabelBottom = -Infinity;
    const lineHeight = 14; 

    // 3. Render
    labels.forEach(l => {{
        // Target Position
        // Overview needs more spacing to right mostly?
        // Shift rightward to avoid map body as much as possible
        const offX = 40; 
        let labelY = l.y; 
        
        // Anti-collision
        if (labelY < lastLabelBottom + 12) {{
             labelY = lastLabelBottom + 12;
        }}
        lastLabelBottom = labelY;

        const labelX = l.x + offX;
        
        // Line
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', l.x);
        line.setAttribute('y1', l.y);
        line.setAttribute('x2', labelX);
        line.setAttribute('y2', labelY - 3);
        line.setAttribute('class', 'label-line');
        group.appendChild(line);
        
        // Text
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', labelX + 5);
        text.setAttribute('y', labelY);
        text.setAttribute('class', 'label-text region-' + l.region);
        text.textContent = `${{l.name}} (${{l.count}})`;
        
        text.onclick = (e) => {{
            e.stopPropagation();
            window.openEventModal(l.events);
        }};
        group.appendChild(text);
    }});

    mapSvg.appendChild(group);
}}

function resetZoom() {{
    const mapSvg = document.getElementById('japan-map');
    mapSvg.setAttribute('viewBox', '0 0 {SVG_WIDTH} {SVG_HEIGHT}'); 
    renderDots(currentMapData.overview, false);
    
    const labels = document.getElementById('zoom-labels');
    if (labels) labels.remove();
    
    renderOverviewLabels(); // Show overview labels

    document.getElementById('reset-zoom').style.display = 'none';
}}

function setupModal() {{
    const modal = document.getElementById('event-modal');
    const span = document.querySelector('.close-modal');
    
    // Close button click handler
    if (span) {{
        span.onclick = () => {{
            modal.style.display = "none";
        }};
    }}
    
    // Click outside modal to close
    modal.addEventListener('click', (event) => {{
        if (event.target === modal) {{
            modal.style.display = "none";
        }}
    }});
}}

function openModal(events) {{
    const modal = document.getElementById('event-modal');
    const body = document.getElementById('modal-body');
    const selection = document.getElementById('modal-selection');
    
    if (!modal || !body || !selection) return;

    body.innerHTML = '';
    selection.innerHTML = '';
    selection.style.display = 'none';
    
    if (events.length === 1) {{
        renderModalContent(events[0]);
    }} else {{
        body.innerHTML = '<h3>複数のイベントがあります</h3><p>詳細を見るイベントを選択してください:</p>';
        selection.style.display = 'block';
        events.forEach(event => {{
            const div = document.createElement('div');
            div.className = 'cluster-option';
            div.textContent = `${{event.name}} (${{event.status === 'visited' ? '参加済み' : '候補'}})`;
            div.onclick = () => {{
                renderModalContent(event);
                selection.style.display = 'none';
            }};
            selection.appendChild(div);
        }});
    }}
    
    modal.style.display = 'block';
}}

// Expose for external calls (e.g. from Event List)
window.openEventModal = (events) => {{
    if (!Array.isArray(events)) events = [events];
    openModal(events);
}};

function renderModalContent(event) {{
    const body = document.getElementById('modal-body');
    const typeLabel = event.status === 'visited' ? '参加済み' : 'いつか参加したい';
    
    let html = `
        <h3>${{event.name}}</h3>
        <p style="color:#aaa; font-size:0.9em; margin-bottom:1rem;">📍 ${{event.location}} | ${{typeLabel}}</p>
        <p>${{event.description || ''}}</p>
    `;
    
    if (event.photos && event.photos.length > 0) {{
        html += `<img src="${{event.photos[0]}}" alt="${{event.name}} photo" style="max-width:100%; height:auto; display:block; margin-top:1rem; border-radius:8px;">`;
    }}
    
    body.innerHTML = html;
}}

let tooltip = null;
function showTooltip(event, text) {{
    if (!tooltip) {{
        tooltip = document.createElement('div');
        tooltip.className = 'map-tooltip';
        document.body.appendChild(tooltip);
    }}
    tooltip.textContent = text;
    tooltip.style.display = 'block';
    
    // Smart Positioning to prevent off-screen
    const w = tooltip.offsetWidth;
    const h = tooltip.offsetHeight;
    const padding = 15;
    
    let x = event.pageX + padding;
    let y = event.pageY + padding;
    
    // Collision with right edge
    if (x + w > window.innerWidth + window.scrollX) {{
        x = event.pageX - w - padding;
    }}
    
    // Collision with bottom edge
    if (y + h > window.innerHeight + window.scrollY) {{
        y = event.pageY - h - padding;
    }}
    
    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
}}
function hideTooltip() {{
    if (tooltip) tooltip.style.display = 'none';
}}
"""

    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print("Done!")

if __name__ == "__main__":
    main()
