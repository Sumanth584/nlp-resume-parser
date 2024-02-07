// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAdJlHpvK6WdmWXmwmeVI615t4p7qeTKeQ",
  authDomain: "final-project-1fc80.firebaseapp.com",
  projectId: "final-project-1fc80",
  storageBucket: "final-project-1fc80.appspot.com",
  messagingSenderId: "312516215725",
  appId: "1:312516215725:web:e70caeaf05fb4c147e9724",
  measurementId: "G-SZQXG304H5"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

export default app;