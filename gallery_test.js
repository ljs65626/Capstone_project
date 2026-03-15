// 갤러리 웹페이지 테스트
describe('슬라이드 갤러리 테스트', () => {
  let galleryFrame;
  let galleryWindow;
  let galleryDocument;

  beforeEach(() => {
    galleryFrame = document.getElementById('gallery-frame');
    galleryWindow = galleryFrame.contentWindow;
    galleryDocument = galleryFrame.contentDocument || galleryFrame.contentWindow.document;
  });

  // DOM 로딩 테스트
  it('모든 슬라이드가 로드되어야 함', () => {
    // 갤러리가 로드되면 DOM에 slide-preview 클래스를 가진 요소가 10개 있어야 함
    const slidePreviews = galleryDocument.querySelectorAll('.slide-preview');
    expect(slidePreviews.length).toBe(10);
  });

  // 네비게이션 테스트
  it('슬라이드 미리보기 클릭 시 해당 슬라이드로 이동해야 함', () => {
    const firstSlidePreview = galleryDocument.querySelector('.slide-preview');
    
    // 클릭 이벤트 트리거
    const clickEvent = galleryDocument.createEvent('MouseEvents');
    clickEvent.initEvent('click', true, true);
    firstSlidePreview.dispatchEvent(clickEvent);
    
    // 모달이 표시되어야 함
    const modal = galleryDocument.querySelector('.slide-modal');
    expect(modal.style.display).toBe('block');
    
    // iframe의 src가 첫 번째 슬라이드를 가리켜야 함
    const modalIframe = galleryDocument.getElementById('modalIframe');
    expect(modalIframe.src.includes('Slide_1.html')).toBe(true);
  });

  // 모달 닫기 테스트
  it('닫기 버튼을 클릭하면 모달이 닫혀야 함', () => {
    // 먼저 모달 열기
    const firstSlidePreview = galleryDocument.querySelector('.slide-preview');
    const clickEvent = galleryDocument.createEvent('MouseEvents');
    clickEvent.initEvent('click', true, true);
    firstSlidePreview.dispatchEvent(clickEvent);
    
    // 모달이 열려있는지 확인
    const modal = galleryDocument.querySelector('.slide-modal');
    expect(modal.style.display).toBe('block');
    
    // 닫기 버튼 클릭
    const closeButton = galleryDocument.getElementById('closeModal');
    const closeEvent = galleryDocument.createEvent('MouseEvents');
    closeEvent.initEvent('click', true, true);
    closeButton.dispatchEvent(closeEvent);
    
    // 모달이 닫혀야 함
    expect(modal.style.display).toBe('none');
  });
  
  // 네비게이션 버튼 테스트
  it('다음 버튼을 클릭하면 다음 슬라이드로 이동해야 함', () => {
    // 먼저 모달 열기
    const firstSlidePreview = galleryDocument.querySelector('.slide-preview');
    const clickEvent = galleryDocument.createEvent('MouseEvents');
    clickEvent.initEvent('click', true, true);
    firstSlidePreview.dispatchEvent(clickEvent);
    
    // 다음 버튼 클릭
    const nextButton = galleryDocument.getElementById('nextSlide');
    const nextEvent = galleryDocument.createEvent('MouseEvents');
    nextEvent.initEvent('click', true, true);
    nextButton.dispatchEvent(nextEvent);
    
    // iframe의 src가 두 번째 슬라이드를 가리켜야 함
    const modalIframe = galleryDocument.getElementById('modalIframe');
    expect(modalIframe.src.includes('Slide_2.html')).toBe(true);
  });
}); 