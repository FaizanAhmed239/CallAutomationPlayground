import React, { useState, useEffect, useRef } from "react";
import withStyles from "@material-ui/core/styles/withStyles";
import Typography from "@material-ui/core/Typography";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import TranscribeOutput from "./TranscribeOutput";
import { ReactMic } from "react-mic";
import axios from "axios";
import { PulseLoader } from "react-spinners";
import { PiRecordFill } from "react-icons/pi";
import { MdOutlinePhonePaused } from "react-icons/md";

const useStyles = () => ({
  root: {
    display: "flex",
    flex: "1",
    margin: "100px 0px 100px 0px",
    alignItems: "center",
    textAlign: "center",
    flexDirection: "column",
  },
  title: {
    marginBottom: "30px",
    textDecoration: "underline",
  },
  settingsSection: {
    marginBottom: "20px",
    display: "flex",
    width: "100%",
  },
  buttonsSection: {
    marginBottom: "40px",
  },
  recordIllustration: {
    width: "100px",
  },
  iconDiv: {
    marginTop: "30px",
    width: "630px",
    display: "flex",
    flexDirection: "row",
    alignItems: "flex-start",
  },
});

const App = ({ classes }) => {
  const [transcribedData, setTranscribedData] = useState([]);
  const [interimTranscribedData] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [stopTranscriptionSession, setStopTranscriptionSession] =
    useState(false);
  const [isFirstPressedText, setIsFirstPressedText] = useState(true);
  const stopTranscriptionSessionRef = useRef(stopTranscriptionSession);
  stopTranscriptionSessionRef.current = stopTranscriptionSession;

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    // Remove the event listener when the component unmounts
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, []);

  const handleKeyDown = (event) => {
    if (event.code === "Space") {
      setIsRecording(true);
      setIsFirstPressedText(false);
      startRecording();
    }
  };

  const handleKeyUp = (event) => {
    if (event.code === "Space") {
      setIsRecording(false);
      stopRecording();
      setIsTranscribing(true);
    }
  };

  function startRecording() {
    setStopTranscriptionSession(false);
  }

  function stopRecording() {
    setStopTranscriptionSession(true);
  }

  function onData(recordedBlob) {
    // console.log(recordedBlob);
  }

  function onStop(recordedBlob) {
    transcribeRecording(recordedBlob);
    setIsTranscribing(true);
  }

  function transcribeRecording(recordedBlob) {
    const headers = {
      "content-type": "multipart/form-data",
    };
    const formData = new FormData();
    formData.append("language", "english");
    formData.append("model_size", "large");
    formData.append("audio_data", recordedBlob.blob, "temp_recording");
    axios
      .post("http://0.0.0.0:8000/transcribe", formData, {
        headers,
      })
      .then((res) => {
        if (res.data.predicted_id !== undefined) {
          setTranscribedData((oldData) => [...oldData, res.data.text]);

          axios
            .get(`http://0.0.0.0:8000/audio/${res.data.predicted_id}`, {
              responseType: "arraybuffer",
            })
            .then((res) => {
              const audioBlob = new Blob([res.data], { type: "audio/mp3" });
              const audioUrl = URL.createObjectURL(audioBlob);
              const audio = new Audio(audioUrl);
              audio.play();
            });
        }
        setIsTranscribing(false);
      });

    if (!stopTranscriptionSessionRef.current) {
      setIsRecording(true);
    }
  }

  return (
    <div className={classes.root}>
      <div className={classes.title}>
        <Typography variant="h3">Call Automation Playground </Typography>
      </div>

      {!isFirstPressedText && !isRecording && (
        <div className={classes.iconDiv}>
          <MdOutlinePhonePaused
            size={25}
            style={{
              marginRight: "20px",
              alignContent: "center",
              justifyContent: "center",
            }}
          />
          Call Paused
        </div>
      )}

      {!isFirstPressedText && isRecording && (
        <div className={classes.iconDiv}>
          <PiRecordFill size={25} color="red" style={{ marginRight: "20px" }} />
          Listening . . . . .
        </div>
      )}

      <div
        className="recordIllustration"
        style={{
          marginTop: 60,
        }}
      >
        <ReactMic
          record={isRecording}
          className="sound-wave"
          onStop={onStop}
          onData={onData}
          strokeColor="#0d6efd"
          backgroundColor="#f6f6ef"
        />
      </div>
      <div
        style={{
          border: "0.5px solid rgba(201,201,201,0.5)",
          paddingTop: 20,
          paddingBottom: 20,
          paddingLeft: 15,
          paddingRight: 15,
          marginTop: 80,
          borderRadius: 8,
          boxShadow:
            "rgba(0, 0, 0, 0.1) 0px 3px 26px 0px, rgba(0, 0, 0, 0.06) 0px 0px 0px 1px",
          width: "40%",
        }}
      >
        <div>
          <div style={{ color: "gray", fontWeight: 500, fontSize: 18 }}>
            {isFirstPressedText &&
              "Press and hold space bar to start conversing."}
          </div>
          <TranscribeOutput
            transcribedText={transcribedData}
            interimTranscribedText={interimTranscribedData}
          />
          <PulseLoader
            sizeUnit={"px"}
            size={20}
            color="purple"
            loading={isTranscribing}
          />
        </div>
      </div>
    </div>
  );
};

export default withStyles(useStyles)(App);
