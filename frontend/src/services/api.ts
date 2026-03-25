const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export interface User {
  id: number;
  name: string;
  registration: string;
  cpf?: string;
  idface_id?: number;
  active: boolean;
  has_photo: boolean;
  photo_url?: string;
  created_at: string;
}

export interface Presence {
  id: number;
  user_id: number;
  name: string;
  registration: string;
  timestamp: string;
  created_at: string;
  entries_count: number;
}

export interface Stats {
  total_users: number;
  present_today: number;
  absent_today: number;
  total_entries_today: number;
}

export interface CreateUserData {
  name: string;
  registration: string;
  cpf?: string;
  photo?: string;
}

export const api = {
  async getUsers(): Promise<User[]> {
    const response = await fetch(`${API_BASE_URL}/api/users`);
    const data = await response.json();
    return data.users;
  },

  async getUser(id: number): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/users/${id}`);
    const data = await response.json();
    return data.user;
  },

  async createUser(userData: CreateUserData): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao criar usuário');
    }
    return data.user;
  },

  async updateUser(id: number, userData: Partial<CreateUserData>): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/users/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao atualizar usuário');
    }
    return data.user;
  },

  async deleteUser(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/users/${id}`, {
      method: 'DELETE',
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao excluir usuário');
    }
  },

  async toggleUserStatus(id: number): Promise<boolean> {
    const response = await fetch(`${API_BASE_URL}/api/users/${id}/toggle-status`, {
      method: 'POST',
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao alterar status');
    }
    return data.active;
  },

  async syncUser(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/users/${id}/sync`, {
      method: 'POST',
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao sincronizar usuário');
    }
  },

  async syncAllUsers(): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/users/sync-all`, {
      method: 'POST',
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao sincronizar usuários');
    }
    return data;
  },

  async getPresenceToday(): Promise<{ presence: Presence[]; stats: Stats }> {
    const response = await fetch(`${API_BASE_URL}/api/presence/today`);
    const data = await response.json();
    return { presence: data.presence, stats: data.stats };
  },

  async getRecentPresence(limit: number = 50): Promise<Presence[]> {
    const response = await fetch(`${API_BASE_URL}/api/presence/recent?limit=${limit}`);
    const data = await response.json();
    return data.presence;
  },

  async getPresenceStats(): Promise<Stats> {
    const response = await fetch(`${API_BASE_URL}/api/presence/stats`);
    const data = await response.json();
    return data.stats;
  },

  async testIdFace(): Promise<{ connected: boolean; session: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/idface/test`);
    return response.json();
  },

  async openDoor(door: number = 0): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/idface/door/open`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ door }),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error('Erro ao abrir porta');
    }
  },

  getUserPhotoUrl(userId: number): string {
    return `${API_BASE_URL}/api/users/${userId}/photo`;
  },
};
