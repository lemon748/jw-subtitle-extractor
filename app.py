from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import time
import logging

app = Flask(__name__)
CORS(app)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'JW Subtitle Extractor API'
    })

@app.route('/convert', methods=['POST'])
def convert_subtitle():
    try:
        data = request.json
        video_url = data.get('url')
        language = data.get('language', 'KO')
        
        logger.info(f"받은 URL: {video_url}")
        
        if not video_url:
            return jsonify({'error': 'URL이 필요합니다'}), 400
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            logger.info("jwsubtitle 사이트 접속 중...")
            page.goto('https://subtitle-c2419.firebaseapp.com/ko/', wait_until='networkidle')
            
            # 언어 선택
            logger.info(f"언어 선택: {language}")
            page.select_option('#languages', language)
            page.wait_for_timeout(500)
            
            # URL 입력
            logger.info("URL 입력 중...")
            page.fill('#url-input', video_url)
            page.wait_for_timeout(1000)
            
            # Paste 버튼 클릭 (URL 입력 활성화)
            paste_button = page.locator('button:has-text("Paste")')
            if paste_button.count() > 0:
                paste_button.click()
                page.wait_for_timeout(500)
            
            # Submit 버튼 찾기 및 클릭
            logger.info("Submit 버튼 클릭 중...")
            
            # 버튼이 활성화될 때까지 대기
            page.wait_for_selector('button.button:not(.is-static):not([disabled])', timeout=10000)
            submit_button = page.locator('button.button:not(.is-static):not([disabled])').first
            submit_button.click()
            
            # 결과 대기
            logger.info("자막 추출 중... (최대 60초)")
            page.wait_for_selector('#result-textarea:not([disabled])', timeout=60000)
            page.wait_for_timeout(2000)  # 추가 대기
            
            # 자막 텍스트 가져오기
            subtitle_text = page.inner_text('#result-textarea')
            
            browser.close()
            
            logger.info("자막 추출 완료!")
            
            if subtitle_text and subtitle_text.strip():
                return jsonify({
                    'success': True,
                    'subtitle': subtitle_text
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '자막을 찾을 수 없습니다'
                }), 404
            
    except Exception as e:
        logger.error(f"에러 발생: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```
