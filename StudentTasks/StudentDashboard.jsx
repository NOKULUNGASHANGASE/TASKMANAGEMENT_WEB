import React, { useEffect, useState } from 'react';

const StudentDashboard = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch('/api/student/tasks/', {
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', 
    })
      .then((res) => res.json())
      .then((resData) => setData(resData))
      .catch((err) => console.error('Failed to fetch dashboard data:', err));
  }, []);

  if (!data) return <div>Loading student dashboard...</div>;

  return (
    <div className="student-dashboard">
      <h2>My Dashboard</h2>

      <section>
        <h3>Submission Progress</h3>
        <p>{data.submission_progress}% complete ({data.submitted_weeks} of {data.total_weeks} weeks)</p>
      </section>

      <section>
        <h3>Completed Tasks</h3>
        <ul>
          {data.completed_tasks.length > 0 ? (
            data.completed_tasks.map((task) => (
              <li key={task.id}>
                {task.title} - Completed on{' '}
                {new Date(task.datecomplited).toLocaleDateString()}
              </li>
            ))
          ) : (
            <li>No completed tasks yet.</li>
          )}
        </ul>
      </section>

      <section>
        <h3>Overdue Weeks</h3>
        <ul>
          {data.overdue_weeks.length > 0 ? (
            data.overdue_weeks.map((week) => (
              <li key={week.week_num}>
                Week {week.week_num}: {week.start_date} - {week.end_date}
              </li>
            ))
          ) : (
            <li>No overdue weeks</li>
          )}
        </ul>
      </section>

      <section>
        <h3>Calendar Events</h3>
        <pre>{JSON.stringify(data.events, null, 2)}</pre>
        {/* Replace this with a calendar component like FullCalendar later */}
      </section>
    </div>
  );
};

export default StudentDashboard;
