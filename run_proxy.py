import os
import urllib.request
from http.server import SimpleHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv
import webbrowser

# .env 파일 로드
load_dotenv()

# 환경변수에서 API 키 가져오기 (Anthropic 또는 OpenAI)
API_KEY = os.getenv("OPENAI_API_KEY")

class ProxyHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # API 이외의 GET 요청은 기본 정적 파일 제공기능 사용
        # 기본 문서를 index.html로 설정
        if self.path == '/':
            self.path = '/index.html'
        
        return super().do_GET()

    def do_POST(self):
        # /api/chat 경로로 POST 요청이 오면 프록시 처리
        if self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # OpenAI API로 요청 포워딩
            req = urllib.request.Request(
                'https://api.openai.com/v1/chat/completions',
                data=post_data,
                headers={
                    'Authorization': f'Bearer {API_KEY}',
                    'Content-Type': 'application/json'
                }
            )
            
            try:
                # API 호출 수행
                with urllib.request.urlopen(req) as response:
                    res_body = response.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(res_body)
            except urllib.error.HTTPError as e:
                # 에러 발생 시 클라이언트(HTML)로 에러 전달
                self.send_response(e.code)
                self.end_headers()
                self.wfile.write(e.read())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    if not API_KEY:
        print("❌ 오류: .env 파일에 OPENAI_API_KEY가 설정되어 있지 않습니다.")
        print("API 키를 설정하고 다시 실행해주세요.")
    else:
        # 고정 포트(예: 8080)로 서버 열기
        PORT = 8080
        server_address = ('', PORT)
        httpd = HTTPServer(server_address, ProxyHandler)
        
        print(f"✅ 로컬 서버가 시작되었습니다! API 키는 백엔드에 안전하게 보관됩니다.")
        print(f"웹 브라우저에서 아래 주소로 접속하세요:")
        print(f"👉 http://localhost:{PORT}/index.html")
        
        # 자동으로 브라우저 열기
        try:
            webbrowser.open(f"http://localhost:{PORT}/index.html")
        except:
            pass
            
        # 서버 무한 대기
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n서버를 종료합니다.")
            httpd.server_close()
