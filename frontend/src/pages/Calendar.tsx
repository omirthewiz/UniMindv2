import React, { useEffect, useState } from "react";
import { Calendar, dateFnsLocalizer, Views, Event, View } from "react-big-calendar";
import "react-big-calendar/lib/css/react-big-calendar.css";
import { format, parse, startOfWeek, getDay, addMonths, subMonths } from "date-fns"; 
import { enUS } from "date-fns/locale"; 

import { 
    getFirestore,
    collection,
    addDoc,
    getDocs,
    doc,
    deleteDoc,
    updateDoc,
    query,
    where,
    orderBy,
    DocumentData,
} from "firebase/firestore";
import { app } from "../firebaseConfig";
import { useAuth0 } from "@auth0/auth0-react"; 
import EventModal from "../components/EventModal"; 

// --- LOCALIZER SETUP ---
const locales = { "en-US": enUS };
const localizer = dateFnsLocalizer({ format, parse, startOfWeek, getDay, locales });
// -----------------------

// --- Define Custom Event Type ---
interface MyEvent extends Event {
    id: string; 
    title: string;
    start: Date;
    end: Date;
}

// --- Custom event component (for click listener) ---
const CustomEvent = (props: any) => {
    const handleEventClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        
        // FIX: The prop you want to call is usually passed as 'onSelect' 
        // to the CustomEvent component by the library. If that fails, 
        // we'll try the generic onClick handler the library provides on props.
        if (typeof props.onClick === 'function') {
            props.onClick(props.event, e);
        } else if (typeof props.onSelect === 'function') {
            // Fallback for previous attempts
            props.onSelect(props.event, e);
        }
        // NOTE: The main component handler (handleSelectEvent) will now fire correctly
        // because the library's internal onClick handler is finally executed.
    };

    return (
        <div 
            onClick={handleEventClick} 
            style={{ height: '100%', cursor: 'pointer' }}
            title={props.event.title}
        >
            {props.title}
        </div>
    );
};

// --- CUSTOM TOOLBAR (FIX FOR BUTTONS) ---
const CustomToolbar = (props: any) => {
    
    const { setCurrentDate, setCurrentView, currentDate, currentView } = props;

    const navigate = (action: 'NEXT' | 'PREV' | 'TODAY') => {
        let newDate = currentDate;
        if (action === 'TODAY') {
            newDate = new Date();
        } else if (action === 'NEXT') {
            newDate = addMonths(currentDate, 1);
        } else if (action === 'PREV') {
            newDate = subMonths(currentDate, 1);
        }
        setCurrentDate(newDate);
    };
    
    const viewChange = (view: View) => {
        setCurrentView(view);
    };
    
    const toolbarLabel = format(props.date, 'MMMM yyyy');

    return (
        <div className="rbc-toolbar mb-4 flex justify-between items-center border-b pb-2">
            
            {/* Left side: Date Navigation */}
            <span className="rbc-btn-group flex gap-2">
                <button 
                    type="button" 
                    className="px-3 py-1 border rounded-md hover:bg-gray-100"
                    onClick={() => navigate('TODAY')}
                >
                    Today
                </button>
                <button 
                    type="button" 
                    className="px-3 py-1 border rounded-md hover:bg-gray-100"
                    onClick={() => navigate('PREV')}
                >
                    Back
                </button>
                <button 
                    type="button" 
                    className="px-3 py-1 border rounded-md hover:bg-gray-100"
                    onClick={() => navigate('NEXT')}
                >
                    Next
                </button>
            </span>

            {/* Center: Current Date Label */}
            <span className="rbc-toolbar-label font-semibold text-lg">
                {toolbarLabel}
            </span>

            {/* Right side: View Toggle */}
            <span className="rbc-btn-group flex gap-1">
                {
                    ['month', 'week', 'day'].map((view: string) => (
                        <button
                            key={view}
                            type="button"
                            className={`px-3 py-1 border rounded-md text-sm transition ${
                                currentView === view ? 'bg-indigo-600 text-white' : 'bg-white hover:bg-gray-100'
                            }`}
                            onClick={() => viewChange(view as View)}
                        >
                            {view.charAt(0).toUpperCase() + view.slice(1)}
                        </button>
                    ))
                }
            </span>
        </div>
    );
};


const CalendarPage: React.FC = () => {
    const { user } = useAuth0();
    const db = getFirestore(app);
    const userId = user?.sub ?? "demo_user";

    // --- STATE FOR DATE AND VIEW CONTROL ---
    const [currentDate, setCurrentDate] = useState(new Date()); 
    const [currentView, setCurrentView] = useState<View>(Views.MONTH); 
    // ----------------------------------------

    const [events, setEvents] = useState<MyEvent[]>([]);
    const [selectedEvent, setSelectedEvent] = useState<MyEvent | null>(null);

    // --- Data Loading (omitted for brevity) ---
    const loadEvents = async () => { 
        const q = query(
            collection(db, "events"),
            where("user_id", "==", userId),
            orderBy("start", "asc")
        );
        
        const snapshot = await getDocs(q);

        const loadedEvents: MyEvent[] = snapshot.docs.map(doc => {
            const data = doc.data() as DocumentData; 

            const getValidDate = (value: any): Date => {
                if (value && typeof value.toDate === 'function') {
                    return value.toDate();
                }
                return new Date(value);
            };

            return {
                id: doc.id,
                title: data.title,
                start: getValidDate(data.start),
                end: getValidDate(data.end),
            } as MyEvent; 
        });

        setEvents(loadedEvents);
    };

    useEffect(() => { loadEvents(); }, [userId]);

    // --- Slot Handler (omitted for brevity) ---
    const handleSelectSlot = async ({ start, end }: { start: Date, end: Date }) => {
        if (selectedEvent) return; 

        console.log("[LOG: SLOT HANDLER] Slot selection triggered.");
        const title = prompt("Enter a title for the new event:"); 
        
        if (!title) return;
        
        const dateFormat = "yyyy-MM-dd'T'HH:mm:ss";
        const startLocalString = format(start, dateFormat);
        const endLocalString = format(end, dateFormat);
        
        await addDoc(collection(db, "events"), {
            user_id: userId,
            title,
            notes: "",
            allDay: false,
            start: startLocalString,
            end: endLocalString,
            created_at: new Date().toISOString()
        });
        loadEvents();
    };


    // --- Modal Action Handler (omitted for brevity) ---
    const handleUpdateOrDelete = async (action: 'update' | 'delete', newTitle?: string) => { 
        if (!selectedEvent) return;
        const eventRef = doc(db, "events", selectedEvent.id); 

        if (action === "delete") {
            await deleteDoc(eventRef);
        } else if (action === "update" && newTitle && newTitle !== selectedEvent.title) {
            await updateDoc(eventRef, { title: newTitle });
        }

        setSelectedEvent(null);
        loadEvents();
    };

    // --- Event Click Handler (Opens modal) ---
    const handleSelectEvent = (event: MyEvent) => {
        console.log(`[LOG: EVENT HANDLER] Event clicked. Opening modal for: ${event.title}`);
        setSelectedEvent(event); 
    };
    
    // Helper to close the modal
    const handleCloseModal = () => {
        setSelectedEvent(null);
    };
    
    // These handlers are still required by the Calendar component signature
    const handleNavigate = (newDate: Date) => {
        setCurrentDate(newDate); 
    };
    
    const handleViewChange = (newView: View) => {
        setCurrentView(newView);
    };


    return (
        <div className="p-8">
            <h2 className="text-3xl font-semibold text-sage-800 mb-6">Calendar</h2>

            <div className="bg-white p-4 rounded-xl border border-sage-200 shadow-sm">
                <Calendar
                    localizer={localizer}
                    events={events}
                    startAccessor="start"
                    endAccessor="end"
                    selectable
                    onSelectEvent={handleSelectEvent}
                    onSelectSlot={handleSelectSlot}
                    
                    // --- CONTROLLED NAVIGATION & VIEW ---
                    date={currentDate} 
                    onNavigate={handleNavigate}
                    view={currentView}
                    onView={handleViewChange}
                    
                    // Force re-render for stability
                    key={`${currentDate.getFullYear()}-${currentDate.getMonth()}-${currentDate.getDate()}-${currentView}`}

                    views={[Views.MONTH, Views.WEEK, Views.DAY]}
                    style={{ height: 600 }}
                    
                    components={{
                        // FIX: Pass required state setters via the toolbar prop
                        toolbar: () => (
                            <CustomToolbar
                                currentDate={currentDate}
                                setCurrentDate={setCurrentDate}
                                currentView={currentView}
                                setCurrentView={setCurrentView}
                                date={currentDate} 
                            />
                        ),
                        // Event component for click handling
                        event: CustomEvent, 
                    }}
                />
            </div>
            
            {/* RENDER THE CUSTOM MODAL CONDITIONALLY */}
            {selectedEvent && (
                <EventModal
                    event={selectedEvent}
                    onClose={handleCloseModal}
                    onAction={handleUpdateOrDelete}
                />
            )}
        </div>
    );
};

export default CalendarPage;