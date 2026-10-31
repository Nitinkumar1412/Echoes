import { initializeApp, getApps, getApp } from 'firebase/app';
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  updateProfile,
  type UserCredential,
} from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'AIzaSyCugQ6nky42fS7EuZJxVjxqThDSVBp2DQ0',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'echoes-c0d47.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'echoes-c0d47',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'echoes-c0d47.firebasestorage.app',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '668493433588',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '1:668493433588:web:d47c2f55c3c537fdb06ca1',
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || 'G-7KQQX6NVQP',
};

// Valid Firebase configuration is ready
export const isFirebaseConfigured = true;

export const app = getApps().length
  ? getApp()
  : initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({
  prompt: 'select_account',
});

export interface FirebaseUserResult {
  idToken: string;
  email: string;
  displayName: string;
  photoURL: string;
}

/**
 * Triggers official Google Sign-In Popup via Firebase Authentication.
 */
export async function signInWithGooglePopup(): Promise<FirebaseUserResult> {
  const result: UserCredential = await signInWithPopup(auth, googleProvider);
  const user = result.user;
  const idToken = await user.getIdToken();

  return {
    idToken,
    email: user.email || '',
    displayName: user.displayName || user.email?.split('@')[0] || 'Google User',
    photoURL: user.photoURL || '',
  };
}

/**
 * Creates a new user with Email and Password in Firebase Authentication.
 */
export async function signUpWithEmailPassword(
  email: string,
  password: string,
  displayName: string
): Promise<FirebaseUserResult> {
  const userCredential: UserCredential = await createUserWithEmailAndPassword(
    auth,
    email,
    password
  );
  const user = userCredential.user;

  if (displayName) {
    try {
      await updateProfile(user, { displayName });
    } catch {
      // profile update error is non-fatal
    }
  }

  const idToken = await user.getIdToken();
  return {
    idToken,
    email: user.email || email,
    displayName: displayName || user.displayName || email.split('@')[0],
    photoURL: user.photoURL || '',
  };
}

/**
 * Signs in an existing user with Email and Password in Firebase Authentication.
 */
export async function signInWithEmailPassword(
  email: string,
  password: string
): Promise<FirebaseUserResult> {
  const userCredential: UserCredential = await signInWithEmailAndPassword(
    auth,
    email,
    password
  );
  const user = userCredential.user;
  const idToken = await user.getIdToken();

  return {
    idToken,
    email: user.email || email,
    displayName: user.displayName || email.split('@')[0],
    photoURL: user.photoURL || '',
  };
}

/**
 * Helper to translate Firebase Auth error codes into friendly user messages.
 */
export function formatFirebaseError(err: any): string {
  if (!err) return 'Authentication failed. Please try again.';
  const code = err.code || '';

  switch (code) {
    case 'auth/email-already-in-use':
      return 'This email address is already registered. Please sign in instead.';
    case 'auth/invalid-email':
      return 'Please enter a valid email address.';
    case 'auth/weak-password':
      return 'Password should be at least 6 characters.';
    case 'auth/user-not-found':
      return 'No account found with this email address.';
    case 'auth/wrong-password':
    case 'auth/invalid-credential':
      return 'Invalid email or password. Please verify and try again.';
    case 'auth/user-disabled':
      return 'This user account has been disabled.';
    case 'auth/operation-not-allowed':
      return 'Email/Password sign-in is not enabled in Firebase Console. Go to Authentication -> Sign-in method -> Email/Password and enable it.';
    case 'auth/too-many-requests':
      return 'Access temporarily blocked due to many failed attempts. Try again later or reset password.';
    case 'auth/popup-closed-by-user':
      return 'Sign-in cancelled: Google popup was closed.';
    case 'auth/popup-blocked':
      return 'Popup blocked by browser. Please allow popups for this site.';
    default:
      return err.message || 'Authentication error occurred.';
  }
}
