import { Injectable } from '@angular/core';
import { ToastController } from '@ionic/angular';

@Injectable({
  providedIn: 'root'
})
export class ToastService {

  constructor(private toastController: ToastController) { }

  async showToast(message: string, color: 'success' | 'danger' | 'warning' = 'success', duration: number = 2000) {
    const toast = await this.toastController.create({
      message,
      duration,
      color,
      position: 'top'
    });
    toast.present();
  }
}
