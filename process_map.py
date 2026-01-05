
import struct
import os
import math

# Configuration
INPUT_BMP = 'assets/img/japan_map_base.bmp'
OUTPUT_JS = 'assets/js/japan-map.js'
DOT_SPACING = 4  # Reduced from 7 for finer detail
THRESHOLD = 200   # Pixel brightness threshold (0-255) for "black" (land)

def read_bmp(filepath):
    # ... (same as before) ...
    with open(filepath, 'rb') as f:
        # Read BMP Header (14 bytes)
        bmp_header = f.read(14)
        if bmp_header[:2] != b'BM':
            raise ValueError("Not a valid BMP file")
            
        pixel_data_offset = struct.unpack('<I', bmp_header[10:14])[0]
        
        # Read DIB Header (40 bytes for BITMAPINFOHEADER)
        dib_header = f.read(40)
        width, height = struct.unpack('<ii', dib_header[4:12])
        bpp = struct.unpack('<H', dib_header[14:16])[0]
        
        if bpp not in [24, 32]:
            raise ValueError(f"Unsupported BPP: {bpp}. Only 24 or 32 bit BMP supported.")
            
        # Handle negative height (top-down BMP)
        is_top_down = height < 0
        height = abs(height)
            
        # Move to pixel data
        f.seek(pixel_data_offset)
        
        # Calculate row size with padding (rows are padded to 4-byte boundaries)
        row_size = math.ceil((width * bpp) / 32) * 4
        
        pixels = []
        # Read pixels
        raw_data = f.read()
        
        for y in range(height):
            if is_top_down:
                row_start = y * row_size
            else:
                row_start = (height - 1 - y) * row_size
                
            row_pixels = []
            for x in range(width):
                pixel_offset = row_start + (x * (bpp // 8))
                
                # BGR format
                b = raw_data[pixel_offset]
                g = raw_data[pixel_offset + 1]
                r = raw_data[pixel_offset + 2]
                
                row_pixels.append((r, g, b))
            pixels.append(row_pixels)
            
        return width, height, pixels

def get_region_from_color(r, g, b):
    # Determine region based on color characteristics
    # Image Colors (Approximate based on observation):
    # Blue: Hokkaido
    # Light Blue/Cyan: Tohoku
    # Green: Kanto
    # Purple: Chubu
    # Yellow: Kansai
    # Orange: Chugoku
    # Light Red/Pink: Shikoku
    # Red: Kyushu/Okinawa (Okinawa distinct if possible, else split by location)
    
    # White background
    if r > 240 and g > 240 and b > 240:
        return None
        
    # Classify
    # Blue dominant (Hokkaido)
    if b > r + 50 and b > g + 50:
        return 'Hokkaido'
        
    # Cyan/Light Blue (Tohoku) - High G and B, Low R
    if g > r + 30 and b > r + 30:
        return 'Tohoku'
        
    # Green dominant (Kanto)
    if g > r + 30 and g > b + 30:
        return 'Kanto'
        
    # Purple (Chubu) - High R and B, Medium/Low G
    if r > g + 20 and b > g + 20:
        return 'Chubu'
        
    # Yellow (Kansai) - High R and G, Low B
    if r > b + 50 and g > b + 50:
        return 'Kansai'
        
    # Orange (Chugoku) - High R, Med G, Low B
    if r > g + 30 and r > b + 50:
        return 'Chugoku'
        
    # Pink/Red (Shikoku/Kyushu) 
    # Kyushu is usually Red, Shikoku Pink?
    # Let's use simple logic: High R, everything else lower.
    if r > g and r > b:
        # Could be Kyushu, Shikoku, or Chugoku if logic overlaps.
        # Check coordinates in the caller for disambiguation if colors are similar.
        return 'RedGroup'
        
    return 'Unknown'

def generate_js(width, height, pixels):
    # Scan all dots first
    all_dots = []
    
    for y in range(0, height, DOT_SPACING):
        for x in range(0, width, DOT_SPACING):
            r, g, b = pixels[y][x]
            
            region_key = get_region_from_color(r, g, b)
            
            if region_key:
                # Disambiguate 'RedGroup' (Kyushu, Shikoku, maybe Okinawa)
                if region_key == 'RedGroup':
                    # Kyushu is left (x < 380)
                    # Shikoku is right (x > 380)
                    if x < 380:
                        if y > 600 and x < 300: region_key = 'Okinawa'
                        else: region_key = 'Kyushu'
                    else:
                        region_key = 'Shikoku'
                        
                # Define Name mappings
                name_map = {
                    'Hokkaido': '北海道',
                    'Tohoku': '東北',
                    'Kanto': '関東',
                    'Chubu': '中部',
                    'Kansai': '関西',
                    'Chugoku': '中国',
                    'Shikoku': '四国',
                    'Kyushu': '九州',
                    'Okinawa': '沖縄',
                    'Unknown': '日本'
                }
                
                # Coordinate fallback for 'Unknown' or missed colors
                if region_key == 'Unknown':
                     if y < 300: region_key = 'Hokkaido'
                     elif y > 500: region_key = 'Kyushu'
                     else: region_key = 'Honshu'
                     
                name = name_map.get(region_key, '日本')
                
                all_dots.append({
                    'x': x,
                    'y': y,
                    'region': region_key,
                    'name': name
                })
    
    final_dots = all_dots


    js_content = f"""// Japan Map Dot Pattern Generator
document.addEventListener('DOMContentLoaded', () => {{
    initMap();
}});

function initMap() {{
    const mapSvg = document.getElementById('japan-map');
    if (!mapSvg) return;
    
    const japanDots = {str(final_dots).replace("'", '"')};
    
    mapSvg.innerHTML = '';
    
    japanDots.forEach(dot => {{
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', dot.x);
        circle.setAttribute('cy', dot.y);
        circle.setAttribute('r', '1.5');
        circle.setAttribute('class', `prefecture region-${{dot.region.toLowerCase()}}`);
        circle.setAttribute('data-name', dot.name);
        circle.setAttribute('data-region', dot.region);
        
        circle.addEventListener('click', (e) => {{
            e.stopPropagation();
            zoomToRegion(dot.region);
        }});
        
        circle.addEventListener('mouseenter', (e) => {{
            showTooltip(e, `${{dot.region}}`);
        }});
        circle.addEventListener('mouseleave', hideTooltip);
        
        mapSvg.appendChild(circle);
    }});
    
    document.querySelector('.map-container').addEventListener('click', () => {{
        resetZoom();
    }});
}}

function zoomToRegion(regionName) {{
    const mapSvg = document.getElementById('japan-map');
    const dots = document.querySelectorAll(`.prefecture[data-region="${{regionName}}"]`);
    if (dots.length === 0) return;
    
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    dots.forEach(dot => {{
        const x = parseFloat(dot.getAttribute('cx'));
        const y = parseFloat(dot.getAttribute('cy'));
        if (x < minX) minX = x;
        if (y < minY) minY = y;
        if (x > maxX) maxX = x;
        if (y > maxY) maxY = y;
    }});
    
    // Custom logic for Okinawa to not zoom too much if it's sparse
    let padding = 50;
    if (regionName === 'Okinawa') padding = 100;

    const width = maxX - minX + (padding * 2);
    const height = maxY - minY + (padding * 2);
    const viewBox = `${{minX - padding}} ${{minY - padding}} ${{width}} ${{height}}`;
    
    mapSvg.style.transition = 'all 0.8s cubic-bezier(0.25, 1, 0.5, 1)';
    mapSvg.setAttribute('viewBox', viewBox);
    
    document.getElementById('reset-zoom').style.display = 'block';
    
    document.querySelectorAll('.prefecture').forEach(p => p.classList.add('faded'));
    dots.forEach(p => p.classList.remove('faded'));
}}

function resetZoom() {{
    const mapSvg = document.getElementById('japan-map');
    // Default ViewBox for 800x800 image
    mapSvg.setAttribute('viewBox', '0 0 800 800'); 
    
    document.getElementById('reset-zoom').style.display = 'none';
    document.querySelectorAll('.prefecture').forEach(p => p.classList.remove('faded'));
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
    tooltip.style.left = event.pageX + 10 + 'px';
    tooltip.style.top = event.pageY + 10 + 'px';
}}
function hideTooltip() {{
    if (tooltip) tooltip.style.display = 'none';
}}
"""
    return js_content


try:
    print(f"Reading {INPUT_BMP}...")
    w, h, px = read_bmp(INPUT_BMP)
    print(f"Image size: {w}x{h}")
    
    print("Generating JS content...")
    js_code = generate_js(w, h, px)
    
    print(f"Writing to {OUTPUT_JS}...")
    with open(OUTPUT_JS, 'w') as f:
        f.write(js_code)
        
    print("Done!")
    
except Exception as e:
    print(f"Error: {e}")
