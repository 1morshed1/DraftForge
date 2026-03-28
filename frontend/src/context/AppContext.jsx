import { createContext, useContext, useReducer, useEffect } from "react";
import { getDocuments, getHealth } from "../api/client";

const AppContext = createContext(null);

const initialState = {
  documents: [],
  currentDocument: null,
  currentDraft: null,
  editHistory: [],
  rules: [],
  health: null,
  loading: {
    documents: false,
    draft: false,
    search: false,
    edit: false,
  },
};

function reducer(state, action) {
  switch (action.type) {
    case "SET_DOCUMENTS":
      return { ...state, documents: action.payload };
    case "SET_CURRENT_DOCUMENT":
      return { ...state, currentDocument: action.payload };
    case "SET_CURRENT_DRAFT":
      return { ...state, currentDraft: action.payload };
    case "SET_EDIT_HISTORY":
      return { ...state, editHistory: action.payload };
    case "SET_RULES":
      return { ...state, rules: action.payload };
    case "SET_HEALTH":
      return { ...state, health: action.payload };
    case "SET_LOADING":
      return {
        ...state,
        loading: { ...state.loading, [action.payload.key]: action.payload.value },
      };
    case "ADD_DOCUMENT":
      return { ...state, documents: [...state.documents, action.payload] };
    case "REMOVE_DOCUMENT":
      return {
        ...state,
        documents: state.documents.filter((d) => d.doc_id !== action.payload),
        currentDocument:
          state.currentDocument?.doc_id === action.payload
            ? null
            : state.currentDocument,
      };
    case "CLEAR_DRAFT":
      return { ...state, currentDraft: null };
    default:
      return state;
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  const refreshDocuments = async () => {
    dispatch({ type: "SET_LOADING", payload: { key: "documents", value: true } });
    try {
      const { data } = await getDocuments();
      dispatch({ type: "SET_DOCUMENTS", payload: data });
    } catch {
      // silently fail — documents list will be empty
    } finally {
      dispatch({ type: "SET_LOADING", payload: { key: "documents", value: false } });
    }
  };

  const checkHealth = async () => {
    try {
      const { data } = await getHealth();
      dispatch({ type: "SET_HEALTH", payload: data });
    } catch {
      // backend unreachable
    }
  };

  useEffect(() => {
    refreshDocuments();
    checkHealth();
  }, []);

  return (
    <AppContext.Provider value={{ state, dispatch, refreshDocuments, checkHealth }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
