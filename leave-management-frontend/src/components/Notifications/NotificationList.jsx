import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './NotificationList.css'; // optional styles

const NotificationList = () => {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    axios.get('/api/notifications')
      .then(res => setNotifications(res.data))
      .catch(err => console.error(err));
  }, []);

  const markAsRead = (id) => {
    axios.patch(`/api/notifications/${id}/read`)
      .then(() => {
        setNotifications(prev =>
          prev.map(n => n.id === id ? { ...n, read: true } : n)
        );
      })
      .catch(err => console.error(err));
  };

  return (
    <div className="notifications">
      {notifications.map(n => (
        <div key={n.id} className={`notification ${n.read ? 'read' : 'unread'}`}>
          <p>{n.message}</p>
          {!n.read && <button onClick={() => markAsRead(n.id)}>Mark as Read</button>}
        </div>
      ))}
    </div>
  );
};

export default NotificationList;
