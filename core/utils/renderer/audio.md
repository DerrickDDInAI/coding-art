# Audio

## Extract audio from video
### By copying audio
ffmpeg -i videofile.mp4 -vn -acodec copy audiofile.aac


## Add audio to video with no sound
ffmpeg \
    -i videofile.mp4 -i audiofile.aac \
    -c:v copy \
    -map 0:v -map 1:a \
    -y output.mp4