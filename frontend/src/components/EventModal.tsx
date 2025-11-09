import React, { useState } from 'react';

// Define the properties the modal component will accept
interface EventModalProps {
    event: { id: string; title: string; start: Date; };
    onClose: () => void;
    onAction: (action: 'update' | 'delete', newTitle?: string) => void;
}

const EventModal: React.FC<EventModalProps> = ({ event, onClose, onAction }) => {
    
    // State to manage the input field value and an error message
    const [currentTitle, setCurrentTitle] = useState(event.title);
    const [error, setError] = useState<string | null>(null);
    
    // Format the date for display
    const formattedDate = event.start.toLocaleString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });

    const handleSave = () => {
        setError(null);
        if (currentTitle.trim() === '') {
            // Replaced alert() with in-modal state for error display
            setError("Title cannot be empty."); 
            return;
        }
        onAction('update', currentTitle);
    };

    const handleDelete = () => {
        // For simple apps, we'll confirm deletion directly, but ideally, this 
        // would be a separate confirmation modal to eliminate window.confirm.
        // We will keep the button logic simple for now and rely on user intent.
        onAction('delete');
    };

    return (
        // Modal Backdrop
        <div style={styles.backdrop}>
            {/* Modal Content */}
            <div style={styles.modalContent}>
                <h3 style={styles.header}>Edit Event: {event.title}</h3>
                <p style={styles.dateText}>{formattedDate}</p>

                <div style={styles.inputGroup}>
                    <label htmlFor="event-title" style={styles.label}>Title</label>
                    <input 
                        id="event-title"
                        type="text"
                        value={currentTitle}
                        onChange={(e) => {
                            setCurrentTitle(e.target.value);
                            setError(null); // Clear error on change
                        }}
                        style={{ ...styles.input, border: error ? '1px solid #dc3545' : '1px solid #ccc' }}
                    />
                    {error && <p style={styles.errorText}>{error}</p>}
                </div>

                <div style={styles.buttonContainer}>
                    <button 
                        onClick={handleDelete}
                        style={{ ...styles.button, ...styles.deleteButton }}
                    >
                        Delete
                    </button>
                    
                    <button 
                        onClick={onClose}
                        style={{ ...styles.button, ...styles.cancelButton }}
                    >
                        Cancel
                    </button>

                    <button 
                        onClick={handleSave}
                        style={{ ...styles.button, ...styles.saveButton }}
                    >
                        Save
                    </button>
                </div>
            </div>
        </div>
    );
};

// Basic inline styles (replace these with your global CSS or utility classes)
const styles: { [key: string]: React.CSSProperties } = {
    backdrop: {
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
        backgroundColor: 'rgba(0, 0, 0, 0.6)', 
        display: 'flex', justifyContent: 'center', alignItems: 'center', 
        zIndex: 1000 
    },
    modalContent: {
        backgroundColor: '#fff', padding: '30px', borderRadius: '12px', 
        width: '90%', maxWidth: '400px', boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
    },
    header: {
        fontSize: '1.5rem', marginBottom: '10px', color: '#333'
    },
    dateText: {
        color: '#666', fontSize: '0.9rem', marginBottom: '20px'
    },
    inputGroup: {
        marginBottom: '20px'
    },
    label: {
        display: 'block', marginBottom: '5px', fontWeight: 'bold'
    },
    input: {
        width: '100%', padding: '10px', borderRadius: '6px', 
        boxSizing: 'border-box'
    },
    errorText: {
        color: '#dc3545',
        marginTop: '5px',
        fontSize: '0.9rem'
    },
    buttonContainer: {
        display: 'flex', justifyContent: 'flex-end', gap: '10px'
    },
    button: {
        padding: '10px 15px', borderRadius: '6px', cursor: 'pointer', border: 'none',
        fontWeight: 'bold'
    },
    deleteButton: {
        backgroundColor: '#dc3545', color: 'white', marginRight: 'auto'
    },
    cancelButton: {
        backgroundColor: '#e9ecef', color: '#333'
    },
    saveButton: {
        backgroundColor: '#007bff', color: 'white'
    }
};

export default EventModal;