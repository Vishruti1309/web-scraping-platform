import { useState, useEffect } from "react";  
import axios from "axios";

function App() {
  const [status, setStatus] = useState("");
  const [data, setData] = useState([]);
  const [search, setSearch] = useState(""); //for search
  const [sortOrder, setSortOrder] = useState("newest"); // for newest sort 
  const [minPrice, setMinPrice] = useState(""); // for price sorting
  const [maxPrice, setMaxPrice] = useState(""); // for price sorting
  const [view, setView] = useState("scraped"); // or "saved"
  const [savedItems, setSavedItems] = useState([]); // Saved button turn grey after saved
  const [activeTab, setActiveTab] = useState("scraped"); // UI of Scraped Data,Saved Jobs
  const API = "https://job-tracker-api-yq7g.onrender.com";

  
    const saveJob = async (job) => {
      try {
        // await axios.post(`${API}/save`, job);
        const res = await axios.post(`${API}/save`, job);

      const filename = res.data.file;

      if (filename) {
        window.open(`${API}/download/${filename}`, "_blank");
      }

        setSavedItems(prev => [...prev, job]); // track saved

      } catch (error) {
        console.error(error);
      }
    };

  const startScraping = async () => {
    setStatus("Starting...");

    
     const res = await axios.post(`${API}/scrape/jobs`);
    const jobId = res.data.job_id;

    setStatus(" Running...");

    checkJobStatus(jobId);
  };

  const checkJobStatus = (jobId) => {
    const interval = setInterval(async () => {
      // const res = await axios.get(`http://127.0.0.1:8000/job/${jobId}`);
      const res = await axios.get(`${API}/job/${jobId}`);

      if (res.data.status === "completed") {
        setStatus("Completed");
        clearInterval(interval);
        fetchData();
      }
    }, 3000);
  };

  const exportAllJobs = async () => {
  try {
    const res = await axios.get(`${API}/export/jobs`);

    const filename = res.data.file;

    if (filename) {
      const link = document.createElement("a");
      link.href = `${API}/download/${filename}`;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

  } catch (error) {
    console.error(error);
  }
};

  const exportCSV = async () => {
  try {
    const res = await axios.get(`${API}/export/jobs`);

    const filename = res.data.file;

    window.open(`${API}/download/${filename}`, "_blank");

  } catch (error) {
    console.error(error);
  }
};

  const fetchData = async () => {
    // const res = await axios.get("http://127.0.0.1:8000/data/books");
    const res = await axios.get(`${API}/data/jobs`);
    setData(res.data);
  };  

//   const fetchSavedJobs = async () => {
//   const res = await axios.get("http://127.0.0.1:8000/saved-jobs");
//   setData(res.data);
// };

    const fetchSavedJobs = async () => {
      try {
        const res = await axios.get(`${API}/saved-jobs`);
        setSavedItems(res.data);
      } catch (err) {
        console.error(err);
      }
    };
    
      useEffect(() => {
        fetchSavedJobs();
      }, []);
  //  Filter +  Price Filter
  const filteredData = data.filter((item) => {
  const titleMatch = item.title
    ?.toLowerCase()
    .includes(search.toLowerCase());

  return titleMatch;
});

  //  Sorting
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
      
     

      {/* FILTER BAR */}
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
        {/*  Search */}
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
        
        <button
  onClick={exportAllJobs}
  style={{
    padding: "10px",
    background: "#10b981",
    color: "white",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer"
  }}
>
  Export All Jobs
</button>
        

        {/*  Sort */}
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

     <div
  style={{
    display: "flex",
    gap: "10px",
    marginTop: "20px",
    background: "#1e293b",
    padding: "6px",
    borderRadius: "10px",
    width: "fit-content"
  }}
>
  {/* Scraped Tab */}
      <button
        onClick={() => setActiveTab("scraped")}
        style={{
          padding: "8px 16px",
          borderRadius: "8px",
          border: "none",
          cursor: "pointer",
          background:
            activeTab === "scraped" ? "#3b82f6" : "transparent",
          color: activeTab === "scraped" ? "white" : "#94a3b8",
          transition: "0.2s"
        }}
      >
        Scraped Data
      </button>

      {/* Saved Tab */}
      <button
        onClick={() => setActiveTab("saved")}
        style={{
          padding: "8px 16px",
          borderRadius: "8px",
          border: "none",
          cursor: "pointer",
          background:
            activeTab === "saved" ? "#3b82f6" : "transparent",
          color: activeTab === "saved" ? "white" : "#94a3b8",
          transition: "0.2s"
        }}
      >
        Saved Jobs
      </button>
    </div>



      {/* <h2>Scraped Data:</h2> */}
      {/* <h2>
        {view === "scraped" ? "Scraped Data" : "Saved Jobs"}  
      </h2> */}

        {/* TAB CONTENT */}

{activeTab === "scraped" && (
  <>
    <p style={{ color: "#94a3b8" }}>
      Showing {sortedData.length} results
    </p>

    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
        gap: "20px",
        marginTop: "20px"
      }}
    >
      {sortedData.map((item, index) => (
        <div
          key={index}
          style={{
            background: "#1e293b",
            padding: "20px",
            borderRadius: "12px",
          }}
        >
          <h3 style={{ color: "#38bdf8" }}>
            {item.title}
          </h3>

          <p>{item.company}</p>

          <p style={{ color: "#94a3b8" }}>
            {item.location}
          </p>

          <p style={{ fontSize: "12px" }}>
            {item.posted_date}
          </p>

          <div style={{ marginTop: "10px", display: "flex", gap: "10px" }}>
            <button
              onClick={() =>
                window.open("https://realpython.github.io/fake-jobs/", "_blank")
              }
              style={{
                flex: 1,
                background: "#22c55e",
                color: "white",
                border: "none",
                padding: "8px",
                borderRadius: "6px",
              }}
            >
              Apply
            </button>

            <button
              onClick={() => saveJob(item)}
              disabled={savedItems.some(job => job.title === item.title)}
              style={{
                flex: 1,
                background: savedItems.some(job => job.title === item.title)
                  ? "#64748b"
                  : "#3b82f6",
                color: "white",
                border: "none",
                padding: "8px",
                borderRadius: "6px",
              }}
            >
              {savedItems.some(job => job.title === item.title) ? "Saved" : "Save"}
            </button>
          </div>
        </div>
      ))}
    </div>
  </>
)}

{activeTab === "saved" && (
  <>
    <h2 style={{ marginTop: "20px" }}>Saved Jobs</h2>

    {savedItems.length === 0 ? (
      <p>No saved jobs yet</p>
    ) : (
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
          gap: "20px",
          marginTop: "20px",
        }}
      >
        {data
          .filter((item) =>
            savedItems.some(job => job.title === item.title) 
          )
          .map((item, index) => (
            <div
              key={index}
              style={{
                background: "#1e293b",
                padding: "20px",
                borderRadius: "12px",
              }}
            >
              <h3 style={{ color: "#38bdf8" }}>
                {item.title}
              </h3>

              <p>{item.company}</p>

              <p style={{ color: "#94a3b8" }}>
                {item.location}
              </p>

              <p style={{ fontSize: "12px" }}>
                {item.posted_date}
              </p>

              <button
                onClick={() =>
                  setSavedItems((prev) =>
                    prev.filter((t) => t !== item.title)
                  )
                }
                style={{
                  marginTop: "10px",
                  background: "#ef4444",
                  color: "white",
                  border: "none",
                  padding: "8px",
                  borderRadius: "6px",
                }}
              >
                Remove
              </button>
            </div>
          ))}
      </div>
    )}
  </>
)}
    </div>
  );
}

export default App;