from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


class FlightFailurePredictor:
    def __init__(self, dataframe):
        self.data = dataframe.copy()
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            random_state=42
        )
        self.if_model = IsolationForest(
            contamination=0.15,
            random_state=42
        )
        self.rf_accuracy = None
        self.if_anomalies = None

    def create_labels(self):
        """
        Create failure-risk labels
        """
        self.data["failure_risk"] = (
            (
                (self.data["engine_temp"] > 0.75) |
                (self.data["airspeed"] > 0.75) |
                (self.data["vertical_speed"] < 0.25)
            )
        ).astype(int)

    def train_random_forest(self):
        """
        Train Random Forest prediction model
        """
        self.create_labels()

        X = self.data.drop("failure_risk", axis=1)
        y = self.data["failure_risk"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            random_state=42
        )

        self.rf_model.fit(X_train, y_train)
        predictions = self.rf_model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        self.rf_accuracy = accuracy

        print(f"Random Forest Accuracy: {accuracy:.2f}")
        return accuracy

    def train_isolation_forest(self):
        """
        Train Isolation Forest anomaly detection
        """
        X = self.data.drop(columns=["failure_risk"], errors="ignore")
        
        predictions = self.if_model.fit_predict(X)
        anomaly_indices = [idx for idx, pred in enumerate(predictions) if pred == -1]
        self.if_anomalies = anomaly_indices

        print(f"Isolation Forest Anomalies: {len(anomaly_indices)}")
        return anomaly_indices

    def train_model(self):
        """
        Train both models for hybrid intelligence
        """
        self.create_labels()
        rf_acc = self.train_random_forest()
        if_anomalies = self.train_isolation_forest()
        
        print("\n=== Hybrid Model Summary ===")
        print(f"Random Forest Accuracy: {rf_acc:.2f}")
        print(f"Isolation Forest Anomalies: {len(if_anomalies)}")
        
        return {
            "rf_accuracy": rf_acc,
            "if_anomalies": len(if_anomalies)
        }

    def predict_failure(self, telemetry_row):
        """
        Predict risk on new telemetry using Random Forest
        """
        prediction = self.rf_model.predict([telemetry_row])
        return prediction[0]

    def detect_anomaly(self, telemetry_row):
        """
        Detect anomaly using Isolation Forest
        """
        prediction = self.if_model.predict([telemetry_row])
        return -1 if prediction[0] == -1 else 0

    def hybrid_risk_assessment(self, telemetry_row):
        """
        Combine both models for hybrid risk intelligence
        """
        rf_risk = self.predict_failure(telemetry_row)
        if_anomaly = self.detect_anomaly(telemetry_row)
        
        combined_risk = (rf_risk + abs(if_anomaly)) / 2
        
        return {
            "rf_risk": rf_risk,
            "if_anomaly": if_anomaly,
            "combined_risk": combined_risk
        }