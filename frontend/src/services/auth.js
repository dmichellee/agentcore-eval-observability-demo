import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
} from 'amazon-cognito-identity-js';
import { fromCognitoIdentityPool } from '@aws-sdk/credential-providers';

// Values come from frontend/.env.local, written by scripts/10-write-frontend-env.sh.
const USER_POOL_ID = process.env.REACT_APP_USER_POOL_ID || '';
const APP_CLIENT_ID = process.env.REACT_APP_APP_CLIENT_ID || '';
const IDENTITY_POOL_ID = process.env.REACT_APP_IDENTITY_POOL_ID || '';
const REGION = process.env.REACT_APP_REGION || 'us-east-1';

// The demo password is random per deployment and stored in Secrets Manager
// (see scripts/06-setup-cognito.sh); it is never committed.
const DEMO_USERNAME = process.env.REACT_APP_DEMO_USERNAME || 'demo@vroomdash.example.com';
const DEMO_PASSWORD = process.env.REACT_APP_DEMO_PASSWORD || '';

if (!USER_POOL_ID || !APP_CLIENT_ID || !IDENTITY_POOL_ID || !DEMO_PASSWORD) {
  // eslint-disable-next-line no-console
  console.error('Missing Cognito settings. Run scripts/10-write-frontend-env.sh and restart npm start.');
}

const userPool = new CognitoUserPool({
  UserPoolId: USER_POOL_ID,
  ClientId: APP_CLIENT_ID,
});

let cachedIdToken = null;
let cachedCredentials = null;
let credentialExpiry = 0;

function authenticateUser(username, password) {
  return new Promise((resolve, reject) => {
    const user = new CognitoUser({
      Username: username,
      Pool: userPool,
    });

    const authDetails = new AuthenticationDetails({
      Username: username,
      Password: password,
    });

    user.authenticateUser(authDetails, {
      onSuccess: (result) => {
        resolve(result);
      },
      onFailure: (err) => {
        reject(err);
      },
      newPasswordRequired: (userAttributes) => {
        // Demo user: auto-complete forced password change with same password
        delete userAttributes.email_verified;
        delete userAttributes.email;
        user.completeNewPasswordChallenge(password, userAttributes, {
          onSuccess: (result) => resolve(result),
          onFailure: (err) => reject(err),
        });
      },
    });
  });
}

export async function getIdToken() {
  if (cachedIdToken) {
    // Check if current session is still valid
    const currentUser = userPool.getCurrentUser();
    if (currentUser) {
      return new Promise((resolve, reject) => {
        currentUser.getSession((err, session) => {
          if (err || !session.isValid()) {
            cachedIdToken = null;
            getIdToken().then(resolve).catch(reject);
            return;
          }
          cachedIdToken = session.getIdToken().getJwtToken();
          resolve(cachedIdToken);
        });
      });
    }
  }

  const session = await authenticateUser(DEMO_USERNAME, DEMO_PASSWORD);
  cachedIdToken = session.getIdToken().getJwtToken();
  return cachedIdToken;
}

export async function getAwsCredentials() {
  const now = Date.now();
  if (cachedCredentials && now < credentialExpiry) {
    return cachedCredentials;
  }

  const idToken = await getIdToken();
  const providerName = `cognito-idp.${REGION}.amazonaws.com/${USER_POOL_ID}`;

  const credentialProvider = fromCognitoIdentityPool({
    identityPoolId: IDENTITY_POOL_ID,
    logins: {
      [providerName]: idToken,
    },
    clientConfig: { region: REGION },
  });

  cachedCredentials = await credentialProvider();
  // Refresh 5 minutes before expiry
  if (cachedCredentials.expiration) {
    credentialExpiry = cachedCredentials.expiration.getTime() - 5 * 60 * 1000;
  } else {
    credentialExpiry = now + 50 * 60 * 1000; // default 50 min
  }

  return cachedCredentials;
}

export function getRegion() {
  return REGION;
}
