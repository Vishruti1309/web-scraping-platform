import { useState } from "react";
import axios from "axios";

function App() {
  const [status, setStatus] = useState("");
  const [data, setData] = useState([]);
  const [search, setSearch] = useState("");
  const [sortOrder, setSortOrder] = useState("newest");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");

  const saveJob = async (job) => {
  try {
    await axios.post("http://127.0.0.1:8000/save", job);
    alert("Saved!");
  } catch (error) {
    console.error(error);
    alert("Failed to save");
  }
};
  const startScraping = async () => {
    setStatus("Starting...");

    const res = await axios.post("http://127.0.0.1:8000/scrape/books");
    const jobId = res.data.job_id;

    setStatus(" Running...");

    checkJobStatus(jobId);
  };

  const checkJobStatus = (jobId) => {
    const interval = setInterval(async () => {
      const res = await axios.get(`http://127.0.0.1:8000/job/${jobId}`);

      if (res.data.status === "completed") {
        setStatus("Completed");
        clearInterval(interval);
        fetchData();
      }
    }, 3000);
  };

  const fetchData = async () => {
    const res = await axios.get("http://127.0.0.1:8000/data/books");
    setData(res.data);
  };

  //  Filter +  Price Filter
  const filteredData = data.filter((item) => {
    const titleMatch = item.title
      ?.toLowerCase()
      .includes(search.toLowerCase());

    const price = parseFloat(item.price);
    const min = minPrice ? parseFloat(minPrice) : 0;
    const max = maxPrice ? parseFloat(maxPrice) : Infinity;

    const priceMatch = price >= min && price <= max;

    return titleMatch && priceMatch;
  });

  // 🔄 Sorting
  const sortedData =
    sortOrder === "newest"
      ? filteredData
      : [...filteredData].reverse();

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100%",
        backgroundColor: "#0f172a",
        color: "white",
        padding: "30px",
      }}
    >
      <h1 style={{ marginBottom: "20px" }}>
        Job Tracker Dashboard 
      </h1>

      <button
        onClick={startScraping}
        style={{
          padding: "10px 20px",
          background: "#3b82f6",
          color: "white",
          border: "none",
          borderRadius: "6px",
          cursor: "pointer",
          marginBottom: "20px",
        }}
      >
        Start Scraping
      </button>

      <p>Status: {status}</p>

      {/* 🔥 FILTER BAR */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          alignItems: "center",
          marginBottom: "25px",
          flexWrap: "wrap",
          background: "#1e293b",
          padding: "15px",
          borderRadius: "10px",
        }}
      >
        {/* 🔍 Search */}
        <input
          type="text"
          placeholder="🔍 Search jobs..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            padding: "10px",
            borderRadius: "6px",
            border: "1px solid #334155",
            background: "#0f172a",
            color: "white",
            width: "220px",
          }}
        />

        {/* 💰 Min */}
        <input
          type="number"
          placeholder="Min ₹"
          value={minPrice}
          onChange={(e) => setMinPrice(e.target.value)}
          style={{
            padding: "10px",
            borderRadius: "6px",
            border: "1px solid #334155",
            background: "#0f172a",
            color: "white",
            width: "120px",
          }}
        />

        {/* 💰 Max */}
        <input
          type="number"
          placeholder="Max ₹"
          value={maxPrice}
          onChange={(e) => setMaxPrice(e.target.value)}
          style={{
            padding: "10px",
            borderRadius: "6px",
            border: "1px solid #334155",
            background: "#0f172a",
            color: "white",
            width: "120px",
          }}
        />

        {/* 🔄 Sort */}
        <button
          onClick={() =>
            setSortOrder(
              sortOrder === "newest" ? "oldest" : "newest"
            )
          }
          style={{
            padding: "10px 16px",
            background: "#22c55e",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          {sortOrder === "newest" ? "⬇ Newest" : "⬆ Oldest"}
        </button>
      </div>

      <h2>Scraped Data:</h2>

      <p style={{ color: "#94a3b8" }}>
        Showing {sortedData.length} results
      </p>

      {/* TABLE */}
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
        }}
      >
        <thead>
          <tr style={{ background: "#1e293b" }}>
            <th style={{ padding: "12px", textAlign: "left" }}>
              Title
            </th>
            <th style={{ padding: "12px", textAlign: "left" }}>
              Price
            </th>
            <th style={{ padding: "12px", textAlign: "left" }}>
              Availability
            </th>
          </tr>
        </thead>

        <tbody>
          {sortedData.map((item, index) => (
            <tr
              key={index}
              style={{
                borderBottom: "1px solid #334155",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.background =
                  "#1e293b")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.background =
                  "transparent")
              }
            >
              <td style={{ padding: "12px" }}>
                {item.title}
              </td>
              <td style={{ padding: "12px" }}>
                ₹{item.price}
              </td>
              <td style={{ padding: "12px" }}>
                {item.availability}
              </td>

              <td style={{ padding: "12px" }}>
                  <button
                    onClick={() => saveJob(item)}
                    style={{
                      padding: "6px 10px",
                      background: "#000080",
                      color: "white",
                      border: "none",
                      borderRadius: "5px",
                      cursor: "pointer"
                    }}
                  >
                     Save
                  </button>
                </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;