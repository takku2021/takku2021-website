const EVENT_DATA = {
    visited: [
        { name: "おきけも！", prefecture: "沖縄県", location: "北谷町", type: "event", lat: 26.3165, lon: 127.7575, photos: [], description: "沖縄で唯一開催されるケモノイベント。", labelSide: 'left' },
        { name: "JMoF(Japan Meeting of Furries)", prefecture: "愛知県", location: "豊橋市", type: "convention", lat: 34.7691, lon: 137.3914, photos: [], description: "日本最大級のケモノコンベンション。", labelConfig: { angle: 80, length: 15 } },
        { name: "琉大祭", prefecture: "沖縄県", location: "琉球大学", type: "school_festival", lat: 26.2527, lon: 127.7665, photos: [], description: "琉球大学の学園祭。今のところメインで参加するイベント。" },
        { name: "紅葉祭", prefecture: "兵庫県", location: "甲子園大学", type: "school_festival", lat: 34.8065, lon: 135.3336, photos: [], description: "甲子園大学の学園祭。工房の方と交流できたりできてとても楽しかった！" },
        { name: "早稲田祭", prefecture: "東京都", location: "早稲田大学", type: "school_festival", lat: 35.7095, lon: 139.7195, photos: [], description: "早稲田大学の大学祭。めっちゃ人多かった。着ぐるみも多かった。" }
    ],
    wishlist: [
        { name: "ちるこん", prefecture: "北海道", location: "札幌市", type: "event", lat: 43.0618, lon: 141.3545, photos: [], description: "北海道の着ぐるみオフ。" },
        { name: "OFFF(Osaka Furry Fun Festa)", prefecture: "大阪府", location: "大阪市", type: "convention", lat: 34.6360, lon: 135.4146, photos: [], description: "大阪で開催されるケモノイベント。", labelConfig: { angle: 90, length: 20 } },
        { name: "Kemocon", prefecture: "静岡県", location: "御殿場市", type: "event", lat: 35.3087, lon: 138.9346, photos: [], description: "御殿場で開催されるコンベンション。", labelConfig: { angle: 45, length: 15 } },
        { name: "Bick", prefecture: "熊本県", location: "熊本市", type: "event", lat: 32.8059, lon: 130.6918, photos: [], description: "熊本のケモノイベント。" },
        { name: "ケモノすてーしょん！", prefecture: "兵庫県", location: "神戸市", type: "event", lat: 34.6849, lon: 135.1987, photos: [], description: "神戸のデザインセンターで開催。", labelConfig: { angle: -125, length: 10 } },
        { name: "アワジール", prefecture: "兵庫県", location: "淡路島", type: "event", lat: 34.3833, lon: 134.8333, photos: [], description: "淡路島でのイベント。", labelConfig: { angle: 150, length: 10 } },
        { name: "獣ヶ島", prefecture: "香川県", location: "高松市 女木島", type: "event", lat: 34.3965, lon: 134.0531, photos: [], description: "女木島（鬼ヶ島）での野外撮影イベント。" }
    ]
};

// Helper to check status
function getPrefectureStatus(prefName) {
    // 1. Check Visited (Priority)
    const visited = EVENT_DATA.visited.some(e => e.prefecture === prefName || prefName.includes(e.prefecture));
    if (visited) return 'visited';

    // 2. Check Wishlist
    const wishlist = EVENT_DATA.wishlist.some(e => e.prefecture === prefName || prefName.includes(e.prefecture));
    if (wishlist) return 'wishlist';

    return null;
}

// Check proximity to specific event locations (Spot Coloring)
function getSpotStatus(lat, lon, thresholdKm = 10) {
    const R = 6371; // Earth radius km
    
    const checkEvents = (list, type) => {
        for (const event of list) {
            if (!event.lat || !event.lon) continue;
            
            const dLat = (event.lat - lat) * Math.PI / 180;
            const dLon = (event.lon - lon) * Math.PI / 180;
            const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                      Math.cos(lat * Math.PI / 180) * Math.cos(event.lat * Math.PI / 180) * 
                      Math.sin(dLon/2) * Math.sin(dLon/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            const d = R * c;
            
            if (d < thresholdKm) return type;
        }
        return null;
    };
    
    // Check Visited first
    const visitedMatch = checkEvents(EVENT_DATA.visited, 'visited');
    if (visitedMatch) return visitedMatch;
    
    // Check Wishlist
    const wishlistMatch = checkEvents(EVENT_DATA.wishlist, 'wishlist');
    if (wishlistMatch) return wishlistMatch;
    
    return null;
}

// Render Events List
document.addEventListener('DOMContentLoaded', () => {
    const renderList = (data, containerId, status) => {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = ''; // Clear existing content
        data.forEach((event, i) => {
            const item = document.createElement('div');
            item.className = 'event-item';
            item.style.cursor = 'pointer'; // Indicate clickable
            item.style.transitionDelay = `${i * 0.1}s`; // Staggered delay
            
            // Add click interaction
            item.onclick = () => {
                if (window.openEventModal) {
                    window.openEventModal({...event, status: status});
                } else {
                    console.warn('Modal function not ready');
                }
            };
            
            // Format Type Label
            let typeLabel = event.type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
            
            item.innerHTML = `
                <h3>${event.name}</h3>
                <p class="location">📍 ${event.location}</p>
                <span class="type-badge">${typeLabel}</span>
                <p class="description">${event.description || ''}</p>
            `;
            
            container.appendChild(item);
        });
    };

    renderList(EVENT_DATA.visited, 'visited-events-grid');
    renderList(EVENT_DATA.wishlist, 'wishlist-events-grid');
});
