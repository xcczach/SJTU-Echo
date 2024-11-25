<template>
    <div>
        <button @click="startRecording" :disabled="isRecording">Start Recording</button>
        <button @click="stopRecording" :disabled="!isRecording">Stop Recording</button>
    
        <audio :src="audioSrc" controls></audio>
    </div>
</template>

<script>
    import { ref } from "vue";

    const isRecording = ref(false); 
    const audioFile = ref(null);
    const audioSrc = ref("");
    let mediaRecorder = null; // MediaRecorder instance
    let audioChunks = []; // store audio data

    const startRecording = async () => {
        try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.onstart = () => {
            isRecording.value = true;
            audioChunks = []; // 清空音频片段
        };

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data); // 收集音频数据
        };

        mediaRecorder.onstop = () => {
            isRecording.value = false;

            // 将音频片段组合为 Blob
            const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
            audioFile.value = audioBlob;

            // 创建音频播放 URL
            audioSrc.value = URL.createObjectURL(audioBlob);
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
    };
</script>

<style>

    .popup {
        position: absolute;
        padding: 10px;
        background-color: rgba(0, 0, 0, 0.8);
        color: white;
        border-radius: 5px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.2);
        white-space: nowrap;
        z-index: 1000;
    }

</style>