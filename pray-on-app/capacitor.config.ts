import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  // 앱 고유 식별자 (Google Play Store 등록 시 사용)
  appId: 'com.prayon.app',
  // 앱 표시 이름
  appName: 'Pray ON',
  // 웹 파일 위치 (HTML/CSS/JS)
  webDir: 'www',
  server: {
    // 안드로이드 앱 내장 웹뷰 사용 (오프라인 접근 허용)
    androidScheme: 'https'
  }
};

export default config;
