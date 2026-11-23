
import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/api/disagreements/";

function App() {
  const [organisation, setOrganisation] = useState("ORG-A");
  const [reason, setReason] = useState("");
  const [sort, setSort] = useState("-value");

  const [disagreements, setDisagreements] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function fetchDisagreements() {
      try {
        setLoading(true);
        setError("");

        const params = new URLSearchParams({
          org: organisation,
          sort: sort,
        });

        if (reason) {
          params.append("reason", reason);
        }

        const response = await fetch(`${API_URL}?${params}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error("Failed to fetch reconciliation data");
        }

        const data = await response.json();

        setDisagreements(data.disagreements || []);
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    fetchDisagreements();

    return () => controller.abort();
  }, [organisation, reason, sort]);

  function getSystemAValue(item) {
    return item.system_a_amount ??
      item.system_a?.amount ??
      0;
  }

  function getSystemBValue(item) {
    if (item.system_b_total != null) {
      return item.system_b_total;
    }

    return (item.system_b_entries || []).reduce(
      (total, entry) => total + Number(entry.amount || 0),
      0
    );
  }

  function formatAmount(value) {
    return Number(value || 0).toFixed(2);
  }

  function getLocation(item) {
    return (
      item.system_a?.location_code ||
      item.system_b_entries?.[0]?.location_code ||
      "N/A"
    );
  }

  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>Reconciliation Dashboard</h1>
          <p>Monitor and investigate reconciliation disagreements</p>
        </div>
      </header>

      <section className="filters">
        <div className="filter-group">
          <label>Organisation</label>
          <select
            value={organisation}
            onChange={(e) => setOrganisation(e.target.value)}
          >
            <option value="ORG-A">ORG-A</option>
            <option value="ORG-B">ORG-B</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Disagreement Reason</label>
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          >
            <option value="">All Reasons</option>
            <option value="MISSING_IN_B">Missing in B</option>
            <option value="ORPHAN_IN_B">Orphan in B</option>
            <option value="DUPLICATE_IN_B">Duplicate in B</option>
            <option value="VALUE_MISMATCH">Value Mismatch</option>
            <option value="LOCATION_MISMATCH">Location Mismatch</option>
            <option value="DATE_MISMATCH">Date Mismatch</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Sort by Value</label>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="-value">Highest First</option>
            <option value="value">Lowest First</option>
          </select>
        </div>
      </section>

      <section className="table-section">
        <div className="table-heading">
          <h2>Disagreement Records</h2>
          <span>{disagreements.length} records</span>
        </div>

        {loading && <p className="status">Loading records...</p>}

        {error && <p className="error">{error}</p>}

        {!loading && !error && disagreements.length === 0 && (
          <p className="empty">No disagreement records found.</p>
        )}

        {!loading && !error && disagreements.length > 0 && (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Reason</th>
                  <th>Record ID</th>
                  <th>Location</th>
                  <th>System A Value</th>
                  <th>System B Value</th>
                  <th>Difference</th>
                </tr>
              </thead>

              <tbody>
                {disagreements.map((item, index) => {
                  const systemA = Number(getSystemAValue(item));
                  const systemB = Number(getSystemBValue(item));
                  const difference = systemB - systemA;

                  return (
                    <tr key={`${item.reference}-${item.reason}-${index}`}>
                      <td>{item.reason}</td>
                      <td>{item.reference || "N/A"}</td>
                      <td>{getLocation(item)}</td>
                      <td>{formatAmount(systemA)}</td>
                      <td>{formatAmount(systemB)}</td>
                      <td>{formatAmount(difference)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}

export default App;
