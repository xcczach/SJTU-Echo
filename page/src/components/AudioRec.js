import { ref } from "vue";

const isRecording = ref(false); 
const audioFile = ref(null);
const audioSrc = ref("");
let mediaRecorder = null; // MediaRecorder instance
let audioChunks = []; // store audio data

const downloadAudio = () => {
    if (audioFile.value) {
        const link = document.createElement("a");
        link.href = audioSrc.value;
        link.download = "audio.mp3";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

const startRecording = async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.onstart = () => {
            isRecording.value = true;
            audioChunks = []; // Clear audio data
        };

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data); // Store audio data
        };

        mediaRecorder.onstop = () => {
            isRecording.value = false;
            const audioBlob = new Blob(audioChunks, { type: "audio/mp3" });
            audioFile.value = audioBlob;
            audioSrc.value = URL.createObjectURL(audioBlob);  // Create a URL for the audio file

            // download the audio file
            downloadAudio();
        };

        mediaRecorder.start();
    } catch (error) {
        console.error("Error accessing microphone:", error);
    }
};

// Stop recording
const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
    }
}

export { isRecording, audioFile, audioSrc, startRecording, stopRecording };