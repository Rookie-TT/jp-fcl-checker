// 加载港口数据
async function loadPorts() {
    try {
        const response = await fetch('data/ports.json');
        return await response.json();
    } catch (e) {
        console.error('Ports load error:', e);
        return [];
    }
}

// 简单日本地址解析（基于关键词 + 规则，非完整 NLP）
function parseAddress(address) {
    const normalized = address.replace(/[\s\u3000]+/g, '').toLowerCase();
    const prefectures = ['神奈川県', '京都府', '東京都', '大阪府']; // 简化示例，可扩展
    const restricted = ['祇園', '銀座', '東山区', '谷中', '国際通り'];
    const whitelist = ['大黒ふ頭', '鶴見区'];

    let prefecture = '', city = '', town = '', rest = normalized;

    // 提取都道府县
    for (let pref of prefectures) {
        if (normalized.includes(pref.toLowerCase())) {
            prefecture = pref;
            rest = normalized.replace(pref.toLowerCase(), '');
            break;
        }
    }

    // 检查限制区/白名单
    const inRestricted = restricted.some(r => normalized.includes(r.toLowerCase()));
    const inWhitelist = whitelist.some(w => normalized.includes(w.toLowerCase()));

    // 模拟道路宽度（实际可集成 OSM API，但纯前端用随机/规则）
    const roadWidth = inWhitelist ? 12 : (inRestricted ? 2.5 : Math.random() * 5 + 2);

    return {
        full: address,
        prefecture,
        city,
        town,
        rest,
        inRestricted,
        inWhitelist,
        roadWidth: Math.round(roadWidth * 10) / 10
    };
}

// Haversine 距离计算
function haversine(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

// 模拟地理编码（基于地址关键词，返回近似经纬）
function geocode(address) {
    const parsed = parseAddress(address);
    // 简化映射：基于关键词返回坐标
    if (parsed.full.includes('横浜') || parsed.full.includes('Yokohama')) return { lat: 35.4518, lng: 139.6857 };
    if (parsed.full.includes('京都') || parsed.full.includes('Kyoto')) return { lat: 35.0116, lng: 135.7681 };
    if (parsed.full.includes('銀座') || parsed.full.includes('Ginza')) return { lat: 35.6716, lng: 139.7644 };
    // 默认东京
    return { lat: 35.6895, lng: 139.6917 };
}

// 检查可达性
function checkAccessibility(parsed, ports) {
    if (parsed.inWhitelist) {
        return { can: true, reason: '港湾工業地区に位置、道路幅12m以上、40HQ対応可能' }; // 港口工业区
    }
    if (parsed.inRestricted) {
        return { can: false, reason: '祇園/銀座などの古街/商業歩行街、コンテナ車進入不可' }; // 限制区
    }
    const can = parsed.roadWidth >= 3.5;
    const reason = can ? `道路幅${parsed.roadWidth}m、40HQ対応可能` : `最近道路幅${parsed.roadWidth}m、コンテナ車進入不可`;
    return { can, reason };
}

// 获取最近港口
function getNearestPort(lat, lng, ports) {
    let nearest = ports[0];
    let minDist = Infinity;
    ports.forEach(port => {
        const dist = haversine(lat, lng, port.lat, port.lng);
        if (dist < minDist) {
            minDist = dist;
            nearest = port;
        }
    });
    const hours = Math.floor(minDist / 30);
    const mins = Math.round((minDist % 30) * 2);
    const timeStr = hours > 0 ? `${hours}時間${mins}分` : `${mins}分`;
    return {
        name: nearest.name,
        code: nearest.code,
        distance: Math.round(minDist * 10) / 10,
        estimatedTime: timeStr
    };
}

// 主检查函数
async function checkAddress() {
    const address = document.getElementById('address').value.trim();
    if (!address) {
        alert('住所を入力してください / Please enter an address');
        return;
    }

    const ports = await loadPorts();
    const parsed = parseAddress(address);
    const coords = geocode(address);
    const accessibility = checkAccessibility(parsed, ports);
    const nearestPort = getNearestPort(coords.lat, coords.lng, ports);

    const output = `
        <p><strong>整箱到達可能か / FCL Accessibility:</strong> <span class="${accessibility.can ? 'ok' : 'no'}">${accessibility.can ? '可能 / Yes' : '不可能 / No'}</span></p>
        <p><strong>理由 / Reason:</strong> ${accessibility.reason}</p>
        <p><strong>最寄り港 / Nearest Port:</strong> ${nearestPort.name} (${nearestPort.code})</p>
        <p><strong>距離 / Distance:</strong> 約${nearestPort.distance}km、<strong>予想牽引時間 / Est. Haul Time:</strong> ${nearestPort.estimatedTime}</p>
    `;

    document.getElementById('output').innerHTML = output;
    document.getElementById('result').classList.remove('hidden');

    // 暗黑模式切换（可选）
    document.body.classList.toggle('dark', document.body.classList.contains('dark'));
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    // 支持 Enter 键提交
    document.getElementById('address').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') checkAddress();
    });
});