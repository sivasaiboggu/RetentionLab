-- No fabricated transactions: this source provides nine-month aggregates only.
-- Status and Customer Value are excluded: status may proxy the outcome, and the
-- publisher does not specify the value formula. Age fields are not model inputs.
CREATE TABLE features AS
WITH clean AS (
  SELECT rowid AS customer_id, "Call  Failure" AS call_failures,
         Complains AS complaint, "Subscription  Length" AS tenure_months,
         "Charge  Amount" AS charge_band, "Seconds of Use" AS usage_seconds,
         "Frequency of use" AS call_count, "Frequency of SMS" AS sms_count,
         "Distinct Called Numbers" AS contacts, "Tariff Plan" AS tariff_plan,
         Churn AS churn
  FROM raw
), engineered AS (
  SELECT *, 1.0 * call_failures / MAX(call_count, 1) AS failure_rate,
         1.0 * usage_seconds / MAX(call_count, 1) AS seconds_per_call,
         NTILE(4) OVER (ORDER BY usage_seconds, customer_id) AS usage_quartile
  FROM clean
)
SELECT e.*, t.plan_name
FROM engineered e JOIN tariff_lookup t USING (tariff_plan);
