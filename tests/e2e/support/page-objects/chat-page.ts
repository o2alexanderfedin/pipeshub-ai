/**
 * Page Object Model for Chat Page.
 *
 * Encapsulates page interactions for better test maintainability.
 */

import { Page, Locator } from '@playwright/test';

export class ChatPage {
  readonly page: Page;
  readonly messageInput: Locator;
  readonly sendButton: Locator;
  readonly verificationCheckbox: Locator;
  readonly verificationStatus: Locator;
  readonly messagesContainer: Locator;

  constructor(page: Page) {
    this.page = page;
    this.messageInput = page.locator('[data-testid="message-input"]');
    this.sendButton = page.locator('[data-testid="send-button"]');
    this.verificationCheckbox = page.locator('[data-testid="verification-checkbox"]');
    this.verificationStatus = page.locator('[data-testid="verification-status"]');
    this.messagesContainer = page.locator('[data-testid="messages-container"]');
  }

  async goto() {
    await this.page.goto('/chat');
  }

  async sendMessage(message: string) {
    await this.messageInput.fill(message);
    await this.sendButton.click();
  }

  async enableVerification() {
    await this.verificationCheckbox.click();
  }

  async waitForResponse() {
    await this.page.waitForSelector('[data-testid="ai-response"]', {
      state: 'visible',
      timeout: 30000,
    });
  }

  async getLastMessage(): Promise<string> {
    const lastMessage = this.messagesContainer.locator('.message').last();
    return await lastMessage.textContent() || '';
  }
}

/**
 * USAGE IN TESTS:
 *
 * import { ChatPage } from '../support/page-objects/chat-page';
 *
 * test('should send message', async ({ page }) => {
 *   const chatPage = new ChatPage(page);
 *   await chatPage.goto();
 *   await chatPage.sendMessage('Hello');
 *   await chatPage.waitForResponse();
 *   expect(await chatPage.getLastMessage()).toContain('Hello');
 * });
 */
