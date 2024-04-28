from scipy.stats import norm
import numpy as np
from scipy.optimize import curve_fit


def sigmoid(x, L, k, x0):
    return L / (1 + np.exp(-k * (x - x0)))


def forecast_vaccination_rates_sigma(
    X, y, initial_guess, days_ahead=90, confidence=0.95
):

    X = np.array(X).ravel()
    y = np.array(y).ravel()

    params, _ = curve_fit(sigmoid, X, y, p0=initial_guess)
    last_index = X.max()
    future_indices = np.array([i for i in range(1, last_index + days_ahead + 1)])
    forecast = sigmoid(future_indices, *params)

    # Confidence interval calculations
    residuals = y - sigmoid(X, *params)
    sigma = np.sqrt(np.sum(residuals**2) / len(X))
    z = norm.ppf((1 + confidence) / 2)

    upper_forecast = forecast + z * sigma
    lower_forecast = forecast - z * sigma

    return future_indices.reshape(-1, 1), forecast, upper_forecast, lower_forecast
