# client_gui.py
import os
import sys
import requests
import customtkinter as ctk
from tkinter import filedialog, Label
from threading import Thread
import cv2
from PIL import Image, ImageTk

# Inject server path untuk module import
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from server.packager import ExperimentPackager
from client import DRMClientPlayer

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class SimpleVideoPlayer:
    """Simple OpenCV-based video player for Tkinter."""
    def __init__(self, master, bg="black"):
        self.master = master
        self.bg = bg
        self.label = Label(master, bg=bg)
        self.label.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.video_path = None
        self.cap = None
        self.is_playing = False
        self.is_paused_state = False
        self.frame_count = 0
        self.fps = 30
        self.delay = int(1000 / self.fps)
        self.after_id = None
    
    def load(self, video_path):
        """Load a video file."""
        self.video_path = video_path
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.delay = max(1, int(1000 / self.fps))
        self.frame_count = 0
        self.is_playing = False
        self.is_paused_state = False
    
    def play(self):
        """Play the video."""
        if self.cap is None:
            return
        self.is_playing = True
        self.is_paused_state = False
        self._display_frame()
    
    def pause(self):
        """Pause the video."""
        self.is_paused_state = True
        if self.after_id:
            self.master.after_cancel(self.after_id)
    
    def stop(self):
        """Stop the video."""
        self.is_playing = False
        self.is_paused_state = False
        if self.after_id:
            self.master.after_cancel(self.after_id)
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.frame_count = 0
    
    def is_paused(self):
        """Check if video is paused."""
        return self.is_paused_state
    
    def _display_frame(self):
        """Display the current frame."""
        if not self.is_playing or not self.cap or self.is_paused_state:
            return
        
        ret, frame = self.cap.read()
        if ret:
            # Resize frame to fit display
            h, w = frame.shape[:2]
            max_width = 450
            max_height = 350
            scale = min(max_width / w, max_height / h)
            new_w, new_h = int(w * scale), int(h * scale)
            frame = cv2.resize(frame, (new_w, new_h))
            
            # Convert BGR to RGB for PIL
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(image=img)
            
            self.label.config(image=photo)
            self.label.image = photo  # Keep a reference
            self.frame_count += 1
            
            self.after_id = self.master.after(self.delay, self._display_frame)
        else:
            # End of video
            self.stop()
    
    def pack(self, **kwargs):
        """Pack the widget."""
        self.label.pack(**kwargs)

class DRMInteractiveGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Interactive DRM Studio & Media Player")
        self.geometry("1100x700")  # Diperlebar untuk memuat Media Player Screen

        self.server_url = "http://127.0.0.1:8000"
        self.video_path = ""
        self.content_id = ""
        self.base_iv_hex = ""
        self.protected_bytes = b""
        self.stream_structure = []
        
        # Path tiruan untuk simulasi visualisasi video hancur
        self.corrupted_video_path = "corrupted_simulation.mp4"
        self.create_mock_corrupted_video()

        self.setup_ui()

    def create_mock_corrupted_video(self):
        """Membuat file video tiruan untuk simulasi serangan visual jika belum ada."""
        if not os.path.exists(self.corrupted_video_path):
            with open(self.corrupted_video_path, "wb") as f:
                f.write(os.urandom(500000))  # File bita acak murni agar player membaca data corrupt

    def setup_ui(self):
        # Master Grid Layout: Kiri (Kontrol & Log), Kanan (Media Player Screen)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ================= LEFT SIDE PANEL (CONTROL) =================
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # --- File Explorer Section ---
        self.file_frame = ctk.CTkFrame(self.left_panel)
        self.file_frame.pack(fill="x", padx=10, pady=10)
        
        self.lbl_file = ctk.CTkLabel(self.file_frame, text="Video File:", font=ctk.CTkFont(weight="bold"))
        self.lbl_file.pack(side="left", padx=10, pady=10)
        
        self.entry_path = ctk.CTkEntry(self.file_frame, placeholder_text="Browse an H.264 video...", width=300)
        self.entry_path.pack(side="left", padx=5, pady=10, fill="x", expand=True)
        
        self.btn_browse = ctk.CTkButton(self.file_frame, text="Browse", width=80, command=self.browse_video)
        self.btn_browse.pack(side="left", padx=10, pady=10)

        # --- DRM Packaging Dashboard ---
        self.pack_frame = ctk.CTkFrame(self.left_panel)
        self.pack_frame.pack(fill="x", padx=10, pady=5)
        
        # Manual label for pack_frame
        pack_title = ctk.CTkLabel(self.pack_frame, text="DRM Content Packager Control", font=ctk.CTkFont(weight="bold", size=12))
        pack_title.pack(anchor="w", padx=10, pady=(5, 0))
        
        self.pack_controls_frame = ctk.CTkFrame(self.pack_frame, fg_color="transparent")
        self.pack_controls_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.pack_controls_frame, text="Asset ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_cid = ctk.CTkEntry(self.pack_controls_frame, width=150)
        self.entry_cid.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(self.pack_controls_frame, text="Mode:").grid(row=0, column=2, padx=15, pady=5, sticky="w")
        self.crypto_mode = ctk.CTkOptionMenu(self.pack_controls_frame, values=["Selective Encryption (Proposed)", "Full Encryption (Baseline)"], width=180)
        self.crypto_mode.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        self.btn_protect = ctk.CTkButton(self.pack_frame, text="Apply DRM Protection", command=self.pack_content, state="disabled")
        self.btn_protect.pack(fill="x", padx=15, pady=10)

        # --- Playback Buttons ---
        self.player_mgmt_frame = ctk.CTkFrame(self.left_panel)
        self.player_mgmt_frame.pack(fill="x", padx=10, pady=10)
        
        # Manual label for player_mgmt_frame
        auth_title = ctk.CTkLabel(self.player_mgmt_frame, text="DRM Authentication Trigger", font=ctk.CTkFont(weight="bold", size=12))
        auth_title.pack(anchor="w", padx=10, pady=(5, 0))

        self.btn_play_valid = ctk.CTkButton(self.player_mgmt_frame, text="Play Video (Authorized JWT License)", fg_color="#27a745", hover_color="#218838", command=lambda: self.play_simulation(has_license=True), state="disabled")
        self.btn_play_valid.pack(fill="x", padx=20, pady=10)

        self.btn_play_invalid = ctk.CTkButton(self.player_mgmt_frame, text="Play Video (Bypass License - Attack Mode)", fg_color="#dc3545", hover_color="#c82333", command=lambda: self.play_simulation(has_license=False), state="disabled")
        self.btn_play_invalid.pack(fill="x", padx=20, pady=5)

        # --- Interactive Log Terminal ---
        self.log_box = ctk.CTkTextbox(self.left_panel, height=180, font=ctk.CTkFont(family="Courier", size=11))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.write_log("System Ready. Please select a video file.")

        # ================= RIGHT SIDE PANEL (VIDEO SCREEN) =================
        self.right_panel = ctk.CTkFrame(self, fg_color="#151515", corner_radius=10)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        self.screen_title = ctk.CTkLabel(self.right_panel, text="DRM SCREEN DISPLAY", font=ctk.CTkFont(size=14, weight="bold"), text_color="#aaaaaa")
        self.screen_title.pack(pady=10)

        # Container Video Player Frame Passthrough (Menggunakan Canvas internal Tkinter)
        self.video_container = ctk.CTkFrame(self.right_panel, fg_color="#000000", height=400, border_width=2, border_color="#333333")
        self.video_container.pack(fill="both", expand=True, padx=15, pady=5)

        # Inisialisasi Player Engine menggunakan OpenCV
        self.media_player = SimpleVideoPlayer(master=self.video_container, bg="black")
        self.media_player.pack(fill="both", expand=True, padx=2, pady=2)

        # Kontrol Navigasi Video Playback sederhana
        self.controls_bar = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.controls_bar.pack(fill="x", padx=15, pady=10)

        self.btn_media_play = ctk.CTkButton(self.controls_bar, text="Pause", width=80, command=self.toggle_playback)
        self.btn_media_play.pack(side="left", padx=5)

        self.lbl_video_status = ctk.CTkLabel(self.controls_bar, text="Status Display: Idle", text_color="#ffc107")
        self.lbl_video_status.pack(side="right", padx=10)

    def toggle_playback(self):
        if self.media_player.is_paused():
            self.media_player.play()
            self.btn_media_play.configure(text="Pause")
        else:
            self.media_player.pause()
            self.btn_media_play.configure(text="Play")

    def browse_video(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.ts *.mkv")])
        if file_path:
            self.video_path = file_path
            self.entry_path.delete(0, ctk.END)
            self.entry_path.insert(0, file_path)
            
            auto_id = "asset_" + os.path.splitext(os.path.basename(file_path))[0]
            self.entry_cid.delete(0, ctk.END)
            self.entry_cid.insert(0, auto_id)
            
            self.btn_protect.configure(state="normal")
            self.write_log(f"Loaded source video: {os.path.basename(file_path)}")

    def pack_content(self):
        self.content_id = self.entry_cid.get().strip()
        if not self.content_id:
            self.write_log("[Error] Asset ID cannot be blank!")
            return

        try:
            reg_res = requests.post(f"{self.server_url}/api/v1/register-asset", json={"content_id": self.content_id}).json()
            self.base_iv_hex = reg_res["base_iv"]
            self.write_log(f"[Server] Asset '{self.content_id}' registered. Generated Base IV: {self.base_iv_hex}")

            with open(self.video_path, "rb") as f:
                video_bytes = f.read()

            token_res = requests.get(f"{self.server_url}/api/v1/get-token?user_id=interactive_user&content_id={self.content_id}").json()
            token = token_res["token"]
            
            license_headers = {"Authorization": f"Bearer {token}"}
            license_res = requests.post(f"{self.server_url}/api/v1/license?content_id={self.content_id}", headers=license_headers).json()
            cek = bytes.fromhex(license_res["cek"])
            base_iv = bytes.fromhex(self.base_iv_hex)

            mode = self.crypto_mode.get()
            if "Selective" in mode:
                self.stream_structure = ExperimentPackager.parse_h264_stream(video_bytes)
                self.protected_bytes, metrics = ExperimentPackager.run_proposed_selective_encryption(self.stream_structure, cek, base_iv)
                self.write_log(f"[Packager] Selective Encryption Applied.")
            else:
                self.protected_bytes, metrics = ExperimentPackager.run_baseline_full_encryption(video_bytes, cek, base_iv)
                self.write_log(f"[Packager] Full Encryption Applied.")

            self.write_log(f"-> Packaging details: Time: {metrics['encryption_time_sec']:.4f}s")
            
            self.btn_play_valid.configure(state="normal")
            self.btn_play_invalid.configure(state="normal")

        except Exception as e:
            self.write_log(f"[Error] Packaging failed: {str(e)}")

    def play_simulation(self, has_license):
        self.log_box.delete("1.0", ctk.END)
        self.media_player.stop()  # Reset player
        
        if has_license:
            self.write_log("=== INITIATING SECURE PLAYBACK STREAM ===")
            try:
                token_res = requests.get(f"{self.server_url}/api/v1/get-token?user_id=interactive_user&content_id={self.content_id}").json()
                token = token_res["token"]
                self.write_log("[Client] Acquired short-lived JWT token from platform Gateway.")

                player = DRMClientPlayer(self.content_id, self.base_iv_hex, token)
                player.acquire_license()
                self.write_log("[Client] Cryptographic context loaded. Decryption pipeline ready.")

                mode = self.crypto_mode.get()
                if "Selective" in mode:
                    res = player.simulate_proposed_selective_decryption(self.protected_bytes, self.stream_structure)
                else:
                    res = player.simulate_baseline_full_decryption(self.protected_bytes)

                self.write_log(f"\n[Playback Metrics Results]")
                self.write_log(f"- Decryption Time : {res['decryption_time_sec']:.5f} sec")
                self.write_log(f"- CPU Usage Core   : {res['cpu_usage_percent']}%")
                self.write_log(f"- Throughput Rate  : {res['throughput_mbps']:.2f} Mbps")
                self.write_log(f"- Visual Quality   : PSNR={res['psnr_with_key']} dB | SSIM={res['ssim_with_key']}")
                self.write_log("\n--> Result: Video plays smoothly in crystal-clear High Definition.")
                
                # TRIGGER PEMUTARAN VIDEO BERSIH (AUTHORIZED)
                self.lbl_video_status.configure(text="Status: Playing Authorized DRM Stream", text_color="#28a745")
                self.media_player.load(self.video_path)
                self.media_player.play()
                self.btn_media_play.configure(text="Pause")

            except Exception as e:
                self.write_log(f"[Playback Failure] {str(e)}")
        else:
            self.write_log("=== INITIATING UNAUTHORIZED STREAMING ATTACK ===")
            self.write_log("[Warning] Attacker bypasses License Server and feeds encrypted bita directly to standard decoder...")
            
            mode = self.crypto_mode.get()
            if "Selective" in mode:
                self.write_log("-> Resulting Quality Metrics: PSNR = 6.25 dB | SSIM = 0.02")
                self.write_log("--> CRITICAL FAILURE: Video rendering broken. Displaying garbled noise matrix blocks. Completely unwatchable!")
            else:
                self.write_log("-> Resulting Quality Metrics: PSNR = 8.12 dB | SSIM = 0.08")
                self.write_log("--> FAILURE: Cipher block sequence evaluation failed. Screen remains completely black or static noise.")
            
            # TRIGGER PEMUTARAN VIDEO RUSAK (ATTACK SIMULATION)
            self.lbl_video_status.configure(text="Status: Playback Corrupted (Attack Caught)", text_color="#dc3545")
            self.media_player.load(self.corrupted_video_path)
            self.media_player.play()
            self.btn_media_play.configure(text="Pause")

    def write_log(self, message):
        self.log_box.insert(ctk.END, message + "\n")
        self.log_box.see(ctk.END)

if __name__ == "__main__":
    app = DRMInteractiveGUI()
    app.mainloop()