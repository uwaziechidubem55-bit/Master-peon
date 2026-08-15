async function openCam(videoEl){
  const stream = await navigator.mediaDevices.getUserMedia({ video: true });
  videoEl.srcObject = stream;
  await videoEl.play();
  return stream;
}
function snap(videoEl, canvasEl){
  canvasEl.width = videoEl.videoWidth;
  canvasEl.height = videoEl.videoHeight;
  canvasEl.getContext('2d').drawImage(videoEl, 0, 0);
  return canvasEl.toDataURL('image/jpeg', 0.8);
}
