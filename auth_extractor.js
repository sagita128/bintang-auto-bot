/**
 * ═══════════════════════════════════════════════════════════════
 *  TELEGRAM MINI APP AUTH EXTRACTOR
 * ═══════════════════════════════════════════════════════════════
 *
 *  Cara pakai:
 *  1. Buka Telegram Web di browser: https://web.telegram.org/k/
 *  2. Login ke akun Telegram lo
 *  3. Buka bot @earn_stars_bot → buka Mini App
 *  4. Tekan F12 → buka tab Console
 *  5. Paste script ini dan tekan Enter
 *  6. Copy hasil yang muncul
 *
 *  Atau bisa juga pakai extension "Bypass Telegram Web" di Kiwi Browser
 * ═══════════════════════════════════════════════════════════════
 */

(function() {
    'use strict';

    console.log(`
╔══════════════════════════════════════════════════════════════╗
║          ⭐ TELEGRAM AUTH EXTRACTOR ⭐                       ║
╚══════════════════════════════════════════════════════════════╝
    `);

    // Method 1: Dari Telegram WebApp object
    function getFromWebApp() {
        try {
            if (window.Telegram && window.Telegram.WebApp) {
                const webapp = window.Telegram.WebApp;
                return {
                    initData: webapp.initData || '',
                    initDataUnsafe: webapp.initDataUnsafe || {},
                    source: 'Telegram.WebApp'
                };
            }
        } catch(e) {}
        return null;
    }

    // Method 2: Dari URL hash/query
    function getFromURL() {
        try {
            // Telegram Mini App biasanya pass initData via postMessage
            const url = new URL(window.location.href);
            const hash = url.hash;

            if (hash && hash.includes('tgWebAppData')) {
                const params = new URLSearchParams(hash.substring(1));
                const data = params.get('tgWebAppData');
                if (data) {
                    return {
                        initData: decodeURIComponent(data),
                        source: 'URL hash'
                    };
                }
            }
        } catch(e) {}
        return null;
    }

    // Method 3: Intercept postMessage
    function interceptPostMessage() {
        return new Promise((resolve) => {
            const handler = (event) => {
                try {
                    const data = event.data;
                    if (data && (data.initData || data.query_id)) {
                        window.removeEventListener('message', handler);
                        resolve({
                            initData: data.initData || '',
                            query_id: data.query_id || '',
                            user_data: data.user || '',
                            hash: data.hash || '',
                            source: 'postMessage intercept'
                        });
                    }
                } catch(e) {}
            };
            window.addEventListener('message', handler);

            // Timeout setelah 5 detik
            setTimeout(() => {
                window.removeEventListener('message', handler);
                resolve(null);
            }, 5000);
        });
    }

    // Method 4: Dari sessionStorage/localStorage
    function getFromStorage() {
        try {
            const keys = ['initData', 'query_id', 'auth_data', 'tgWebAppData'];
            for (const key of keys) {
                const val = sessionStorage.getItem(key) || localStorage.getItem(key);
                if (val) {
                    return { initData: val, source: `storage[${key}]` };
                }
            }
        } catch(e) {}
        return null;
    }

    // Parse initData ke components
    function parseInitData(initData) {
        if (!initData) return {};

        const params = new URLSearchParams(initData);
        const result = {};

        for (const [key, value] of params) {
            if (key === 'user') {
                try {
                    result.user = JSON.parse(decodeURIComponent(value));
                } catch(e) {
                    result.user_raw = value;
                }
            } else {
                result[key] = value;
            }
        }

        return result;
    }

    // Main extraction
    async function extract() {
        let authData = null;

        // Coba semua method
        authData = getFromWebApp();
        if (!authData) authData = getFromURL();
        if (!authData) authData = getFromStorage();
        if (!authData) authData = await interceptPostMessage();

        if (!authData || !authData.initData) {
            console.error('❌ Tidak bisa extract auth data!');
            console.log('Pastikan Mini App sedang terbuka di Telegram Web');
            console.log('Coba refresh halaman dan buka Mini App lagi');
            return;
        }

        const parsed = parseInitData(authData.initData);

        console.log('\n✅ Auth Data Berhasil Di-Extract!\n');
        console.log('═'.repeat(50));

        // Output untuk config.json
        const configData = {
            query_id: parsed.query_id || '',
            user_data: JSON.stringify(parsed.user || {}),
            hash: parsed.hash || '',
            auth_date: parsed.auth_date || '',
        };

        console.log('\n📋 Copy ini ke config.json:\n');
        console.log(JSON.stringify(configData, null, 2));

        console.log('\n' + '═'.repeat(50));
        console.log('\n📄 Full initData (untuk debugging):\n');
        console.log(authData.initData);

        if (parsed.user) {
            console.log('\n' + '═'.repeat(50));
            console.log('\n👤 User Info:\n');
            console.log(`  ID         : ${parsed.user.id}`);
            console.log(`  Name       : ${parsed.user.first_name} ${parsed.user.last_name || ''}`);
            console.log(`  Username   : @${parsed.user.username || 'N/A'}`);
            console.log(`  Language   : ${parsed.user.language_code || 'N/A'}`);
        }

        console.log('\n' + '═'.repeat(50));
        console.log(`\n📌 Source: ${authData.source}`);
        console.log('\n⚠️  Auth data expire dalam beberapa jam!');
        console.log('   Extract ulang jika bot error 401/403\n');

        // Auto-copy ke clipboard jika tersedia
        try {
            await navigator.clipboard.writeText(JSON.stringify(configData, null, 2));
            console.log('✅ Sudah di-copy ke clipboard!');
        } catch(e) {
            console.log('ℹ️  Manual copy dari console di atas');
        }

        // Return data untuk penggunaan programmatic
        return configData;
    }

    // Jalankan
    extract();
})();
